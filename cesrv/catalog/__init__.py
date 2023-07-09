#!/usr/bin/env python3

import os
import json
import uuid
from dotenv import load_dotenv
from rdflib import Graph, URIRef
from flask import Flask, request, jsonify, abort
from flask_migrate import Migrate
from flask_cors import CORS, cross_origin
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()
import config

from api import api_rest, api_bp
from session import *
from note.sql import *
from note.database import db, checkout_listener
from note.rdf_database import *

app = Flask(__name__)
app.config.from_object('config.{}'.format(config.flask_config))
app.register_blueprint(api_bp)

if app.config['LOGSTASH_HOST'] is not None:
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
SQLDatabase('default', db.get_engine(app=app), dialect='mysql')

virtuoso = SPARQLEndpoint(app.config['RDF_SPARQL'])
graphdb = SPARQLBackend(virtuoso, default_graph=URIRef(app.config['RDF_CONTEXT']))
RDFDatabase[0] = graphdb
