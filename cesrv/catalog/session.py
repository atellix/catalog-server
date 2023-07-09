import sys
import time
from functools import wraps
from datetime import datetime, timedelta
from uuid import uuid4
try:
    import cPickle as pickle
except ImportError:
    import pickle

from flask import request, current_app as app
from flask.sessions import SessionInterface as FlaskSessionInterface
from flask.sessions import SessionMixin
from werkzeug.datastructures import CallbackDict
from itsdangerous import Signer, BadSignature, want_bytes

#from note.models import Session
from note.sql import *
from note.logging import *

def total_seconds(td):
    return td.days * 60 * 60 * 24 + td.seconds

def disable_session(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        setattr(request, 'disable_session', True)
        return function(*args, **kwargs)
    return wrapper

class ServerSideSession(CallbackDict, SessionMixin):
    """Baseclass for server-side based sessions."""

    def __init__(self, initial=None, sid=None, permanent=None):
        def on_update(self):
            self.modified = True
        CallbackDict.__init__(self, initial, on_update)
        self.sid = sid
        if permanent:
            self.permanent = permanent
        self.modified = False

class SqlAlchemySession(ServerSideSession):
    pass

class SessionInterface(FlaskSessionInterface):
    def _generate_sid(self):
        return str(uuid4())

    def _get_signer(self, app):
        if not app.secret_key:
            return None
        return Signer(app.secret_key, salt='flask-session', key_derivation='hmac')

class SqlAlchemySessionInterface(SessionInterface):
    """Uses the note database as a backend

    :param db: A note database
    :param key_prefix: A prefix that is added to all store keys.
    :param use_signer: Whether to sign the session id cookie or not.
    :param permanent: Whether to use permanent session or not.
    """

    serializer = pickle
    session_class = SqlAlchemySession

    def __init__(self, app, db, key_prefix, use_signer=False, permanent=True):
        self.db = db
        self.key_prefix = key_prefix
        self.use_signer = use_signer
        self.permanent = permanent

    def open_session(self, app, request):
        #print('OPEN SESSION')
        if getattr(request, 'disable_session', False):
            #print('SESSION DISABLED')
            return self.session_class()
        sid = request.cookies.get(app.session_cookie_name)
        if not sid and request.is_json:
            sid = request.json.get(app.session_cookie_name, None)
        if not sid:
            sid = self._generate_sid()
            return self.session_class(sid=sid, permanent=self.permanent)
        if self.use_signer:
            signer = self._get_signer(app)
            if signer is None:
                return None
            try:
                sid_as_bytes = signer.unsign(sid)
                sid = sid_as_bytes.decode()
            except BadSignature:
                sid = self._generate_sid()
                return self.session_class(sid=sid, permanent=self.permanent)

        store_id = self.key_prefix + sid
        saved_session = sql_row('client_session', session_id=store_id)
        if saved_session.exists() and saved_session['expiry'] <= datetime.utcnow():
            # Delete expired session
            saved_session.delete()
            saved_session = None
        if saved_session is not None and saved_session.exists():
            try:
                val = saved_session['data']
                data = self.serializer.loads(want_bytes(val))
                return self.session_class(data, sid=sid)
            except:
                return self.session_class(sid=sid, permanent=self.permanent)
        return self.session_class(sid=sid, permanent=self.permanent)

    def save_session(self, app, session, response):
        #print('SAVE SESSION')
        if getattr(request, 'disable_session', False):
            #print('SESSION DISABLED')
            return self.session_class()
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        store_id = self.key_prefix + session.sid
        saved_session = sql_row('client_session', session_id=store_id)
        if not session:
            if session.modified:
                if saved_session.exists():
                    saved_session.delete()
                response.delete_cookie(app.session_cookie_name, domain=domain, path=path)
            return
        httponly = self.get_cookie_httponly(app)
        secure = False # DEV ONLY!
        #secure = self.get_cookie_secure(app)
        #expires = self.get_expiration_time(app, session)
        expires = datetime.utcnow() + timedelta(days=30)
        val = self.serializer.dumps(dict(session))
        uid = None
        if '_user_id' in session:
            uid = session['_user_id']
        if saved_session.exists():
            #log_warning('Update session: {} uid: {}'.format(saved_session['session_id'], uid))
            cuid = saved_session['user_id']
            if uid is not None:
                if cuid is None:
                    # Log-in
                    sql_insert('client_session_log', {
                        'note_session_id': saved_session.sql_id(),
                        'session_id': saved_session['session_id'],
                        'event_name': 'user_login',
                        'user_id': uid,
                        'ts_log': sql_now(),
                        'ip_address': request.remote_addr,
                        'user_agent': request.headers.get('User-Agent'),
                    })
                elif cuid != uid:
                    # Change user
                    sql_insert('client_session_log', {
                        'note_session_id': saved_session.sql_id(),
                        'session_id': saved_session['session_id'],
                        'event_name': 'user_switch',
                        'user_id': uid,
                        'ts_log': sql_now(),
                        'ip_address': request.remote_addr,
                        'user_agent': request.headers.get('User-Agent'),
                    })
            elif cuid is not None:
                sql_insert('client_session_log', {
                    'note_session_id': saved_session.sql_id(),
                    'session_id': saved_session['session_id'],
                    'event_name': 'user_logout',
                    'user_id': cuid,
                    'ts_log': sql_now(),
                    'ip_address': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent'),
                })
                # Log-out
            # Only update expiry if expiry is within 30 minutes
            tdelta = saved_session['expiry'] - sql_now()
            tdmins = tdelta.seconds // 60 % 60
            if tdmins > 30:
                expires = saved_session['expiry']
            else:
                sql_insert('client_session_log', {
                    'note_session_id': saved_session.sql_id(),
                    'session_id': saved_session['session_id'],
                    'event_name': 'session_extend',
                    'user_id': uid,
                    'ts_log': sql_now(),
                    'ip_address': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent'),
                })
            if saved_session['data'] != val or saved_session['expiry'] != expires or saved_session['user_id'] != uid:
                #log_warn('Update session: {} {} {}'.format(val, expires, uid))
                saved_session.update({
                    'data': val,
                    'expiry': expires,
                    'user_id': uid,
                })
            #else:
            #    log_warn('No update for session')
        else:
            #log_warning('Create session: {} uid: {}'.format(store_id, uid))
            new_session = sql_insert('client_session', {
                'session_id': store_id,
                'data': val,
                'expiry': expires,
                'user_id': uid,
            })
            sql_insert('client_session_log', {
                'note_session_id': new_session.sql_id(),
                'session_id': new_session['session_id'],
                'event_name': 'session_create',
                'user_id': uid,
                'ts_log': sql_now(),
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent'),
            })
            if uid is not None:
                sql_insert('client_session_log', {
                    'note_session_id': new_session.sql_id(),
                    'session_id': new_session['session_id'],
                    'event_name': 'user_login',
                    'user_id': uid,
                    'ts_log': sql_now(),
                    'ip_address': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent'),
                })
        if self.use_signer:
            session_id = self._get_signer(app).sign(want_bytes(session.sid))
        else:
            session_id = session.sid
        response.set_cookie(app.session_cookie_name, session_id, expires=expires, httponly=httponly, domain=domain, path=path, secure=secure)

