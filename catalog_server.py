#!/usr/bin/env python3

import os
import json
import uuid
from rdflib import Graph, URIRef
from flask import Flask, request, jsonify, abort
from flask_cors import CORS, cross_origin

os.environ['DB_DATABASE'] = 'atellix_catalog'
os.environ['DB_USER'] = 'catalog'
os.environ['DB_HOST'] = 'atx2.atellix.net'
os.environ['DB_PORT'] = '3306'
os.environ['CATALOG_PROGRAM'] = 'CTLG5CZje37UKZ7UvXiXy1WnJs37npJHxkYXFsEcCCc1'
os.environ['CATALOG_SIGNER'] = 't9ms0xnppf2wdfr8aejhs757y8neq5aad9bedkq58ekgb0th83dn118jp0jj78q19sxkz0m1x02e70h9d78brm7d34m3rt8wjt3dq90'
os.environ['CATALOG_FEE_MINT'] = 'USDVXgXZcQWycX4PAu2CZbGaSG1Ft5rNjo4ARpoqw7w'
os.environ['CATALOG_FEE_ACCOUNT'] = '6sGyBbpzTBaJ5U1kxmdhA9wpfxjcVQ5mymUJcWFCqwSt'
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

