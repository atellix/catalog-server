#!/usr/bin/env python3

import os
import json
import uuid
from dotenv import load_dotenv
from rdflib import Graph, URIRef
from flask import Flask, request, jsonify, abort
from flask_cors import CORS, cross_origin

load_dotenv()
import config

from api import api_rest, api_bp
from note.sql import *
from note.database import db, checkout_listener

app = Flask(__name__)
app.config.from_object('config.{}'.format(config.flask_config))
app.register_blueprint(api_bp)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
db.init_app(app)
SQLDatabase('default', db.get_engine(app=app), dialect='mysql')

