import json
import uuid
import pprint
import traceback
from jose import jwt
from jwcrypto import jwk
from flask import current_app as app, g, abort
from rdflib import Graph, URIRef

from note.logging import *
from note.sql import *
from util import *

CATALOG_BACKENDS = {
    'vendure': True,
}

class CatalogUser():
### Input:
# label
# pubkey
# uri
# uuid
# merchant_data
# backends
#  [[backend_name, {config}]]
    @staticmethod
    def create_user(userinfo):
        nsql.begin()
        try:
            n = sql_now()
            merchant_xml = userinfo['merchant_data']
            mdata = Graph()
            mdata.parse(data=merchant_xml, format='xml')
            sr = sql_insert('user', {
                'active': True,
                'merchant_data': mdata.serialize(format='json-ld'),
                'merchant_label': userinfo['label'],
                'merchant_pk': userinfo.get('pubkey', None),
                'merchant_uri': userinfo['uri'],
                'ts_created': n,
                'ts_updated': n,
                'uuid': userinfo['uuid'],
            })
            if 'backends' in userinfo:
                for bk in userinfo['backends']:
                    if bk[0] not in CATALOG_BACKENDS:
                        raise Exception('Invalid backend: {}'.format(bk[0]))
                    cfg = {}
                    if bk[0] == 'vendure':
                        cfg['vendure_url'] = bk[1]['vendure_url']
                    sql_insert('user_backend', {
                        'user_id': sr.sql_id(),
                        'backend_name': bk[0],
                        'config_data': json.dumps(cfg),
                    })
            log_warn('User Created: {}'.format(sr.sql_id()))
            nsql.commit()
        except Exception as e:
            nsql.rollback()
            raise e
        return sr

    @staticmethod
    def update_user(userinfo):
        nsql.begin()
        try:
            n = sql_now()
            merchant_xml = userinfo['merchant_data']
            mdata = Graph()
            mdata.parse(data=merchant_xml, format='xml')
            sr = sql_row('user', uuid=uuid.UUID(userinfo['uuid']).bytes)
            if not(sr.exists()):
                raise Exception('Invalid user uuid: {}'.format(userinfo['uuid']))
            sr.update({
                'merchant_data': mdata.serialize(format='json-ld'),
                'merchant_label': userinfo['label'],
            })
            log_warn('User Updated: {}'.format(sr.sql_id()))
            nsql.commit()
        except Exception as e:
            nsql.rollback()
            raise e
        return sr

    @staticmethod
    def authorize_user(token):
        try:
            options = {'verify_signature': True, 'exp': True}
            pem = "-----BEGIN CERTIFICATE----- \n{}\n-----END CERTIFICATE----- ".format(app.config['KEYCLOAK_RS256_PUBLIC']).encode('utf8')
            jk = jwk.JWK.from_pem(pem)
            userinfo = jwt.decode(token, jk, algorithms=['RS256'], options=options, audience='account')
            if not(isinstance(userinfo['aud'], list)) or userinfo['aud'][0] != 'account' or userinfo['aud'][1] != app.config['KEYCLOAK_CLIENT']:
                raise Exception('Invalid audience: {} for token: {}'.format(userinfo['aud'], token))
            #log_warn('User Info: {}'.format(userinfo))
            uuid_bin = uuid.UUID(userinfo['sub']).bytes
            rc = SQLRow('user', uuid=uuid_bin)
            if not(rc.exists()):
                raise Exception('User does not exist for uuid: {}'.format(userinfo['sub']))
            if not(rc['active']):
                raise Exception('User not active for uuid: {}'.format(userinfo['sub']))
            log_warn('User Authorized: {}'.format(rc.sql_id()))
            return rc
        except Exception as e:
            etxt = "{}: {}\n{}".format(type(e).__name__, e, ''.join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)[0:-1]))
            log_warn('Login Error: {}'.format(etxt))
            abort(403)
            #return None

    @staticmethod
    def authorize_admin(token, scope, spec):
        #log_warn('Token: {}'.format(token))
        #log_warn('Spec: {}'.format(spec))
        try:
            if scope == 'admin':
                pub = JWKey.from_custom(app.config['AUTH_ADMIN_JWK'])
            elif scope == 'solana':
                pub = JWKey.from_custom(app.config['AUTH_SOLANA_JWK'])
            else:
                raise Exception('Invalid scope: {}'.format(scope))
            vtoken = JWToken(token)
            claims = vtoken.claims(pub)
            for k in sorted(spec.keys()):
                if claims[k] != spec[k]:
                    raise Exception('Claim does not match: {}: {} != {}'.format(k, claims[k], spec[k]))
            #log_warn('Admin authorized')
            return True
        except Exception as e:
            etxt = "{}: {}\n{}".format(type(e).__name__, e, ''.join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)[0:-1]))
            log_warn('Login Error: {}'.format(etxt))
            abort(403)
 
def authorize_user(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if not(len(auth) and auth.startswith('Bearer ')):
            abort(403)
        token = auth[7:]
        g.user = CatalogUser.authorize_user(token)
        return function(*args, **kwargs)
    return wrapper

def authorize_admin(scope, spec):
    def wrapper_outer(function):
        @wraps(function)
        def wrapper_inner(*args, **kwargs):
            auth = request.headers.get('Authorization', '')
            if not(len(auth) and auth.startswith('Bearer ')):
                abort(403)
            token = auth[7:]
            CatalogUser.authorize_admin(token, scope, spec)
            return function(*args, **kwargs)
        return wrapper_inner
    return wrapper_outer

