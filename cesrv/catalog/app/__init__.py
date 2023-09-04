#!/usr/bin/env python3

import os
import json
import uuid
from dotenv import load_dotenv
from rdflib import Graph, URIRef
from flask import Flask, request, jsonify, abort
from flask_request_id import RequestID
from flask_migrate import Migrate
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

import app.config

from app.session import *
from app.api import api_rest, api_bp
from note.sql import *
from note.database import db, checkout_listener
from note.rdf_database import *

app = Flask(__name__)
app.config.from_object('app.config.{}'.format(config.flask_config))
app.register_blueprint(api_bp)

if 'LOGSTASH_HOST' in app.config and app.config['LOGSTASH_HOST'] is not None:
    lhost = app.config['LOGSTASH_HOST']
    lport = int(app.config['LOGSTASH_PORT'])
    handler = logstash.TCPLogstashHandler(lhost, lport, version=1)
    app.logger.addHandler(handler)

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
db.init_app(app)
migrate = Migrate(app, db)

# Session DB
app.session_interface = SqlAlchemySessionInterface(
    app, db,
    app.config['SESSION_KEY_PREFIX'],
    app.config['SESSION_USE_SIGNER'],
    app.config['SESSION_PERMANENT']
)

# MySQL Database
SQLDatabase('default', db.get_engine(app=app), dialect=os.environ.get('DB_DIALECT', 'mysql'))

virtuoso = SPARQLEndpoint(app.config['RDF_SPARQL'])
graphdb = SPARQLBackend(virtuoso, default_graph=URIRef(app.config['RDF_CONTEXT']))
RDFDatabase[0] = graphdb

# Logging generators
def request_id_generator():
    return str(uuid.uuid4())
RequestID(app, generator_func=request_id_generator)

@app.before_request
def request_begin():
    #log_warning('DB Connect')
    nsql.connect()
    #g.keycloak = keycloak_admin
    g.timestamp = time.time_ns()
    g.log = ''

@app.teardown_request
def request_complete(response):
    if getattr(g, 'disable_log_info', False):
        return    
    try:
        cur = time.time_ns()
        st = g.timestamp
        seconds = (cur - st) / (10 ** 9)
        pagelog = g.log.strip()
        res = {
            'githash': app.config['GITHASH'],
            'runtime': seconds,
        }
        if len(pagelog) == 0:
            pagelog = 'Request completed in {} seconds'.format(seconds)
        if current_user.is_authenticated and current_user.is_active:
            res['user_id'] = current_user.id
        log_info(pagelog, extra=res)
    except:
        pass

@app.errorhandler(Exception)
def handle_exception(ex):
    tbtxt = ''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)[0:-1])
    data = { 'traceback': '{}{}: {}'.format(tbtxt, type(ex).__name__, ex) }
    if request.json:
        data['request_json'] = str(pprint.pformat(request.json))
    elif request.form:
        data['request_form'] = str(request.form)
    elif request.data:
        data['request_data'] = str(request.data)
    log_error('Exception: {}'.format(ex), extra = data)
    if isinstance(ex, HTTPException):
        return ex
    print(type(ex).__name__)
    print(tbtxt)
    tbtxt = "<html><body><pre>{}\n{}: {}</pre></body></html>".format(tbtxt, type(ex).__name__, ex)
    return tbtxt, 500

