""" Global Flask Application Settings """

import os
import json
import string
import random
from datetime import datetime, timedelta
from werkzeug.utils import import_string

class Config(object):
    # Flask settings
    DEBUG = os.environ.get('DEBUG', '')
    BASE_DIR = os.path.dirname(__file__)
    SECRET_KEY = os.environ.get('SECRET_KEY', ''.join(random.choices(string.ascii_uppercase + string.digits, k=32)))

    # Flask-SQLAlchemy settings
    DB_API = os.getenv('DB_API', 'mysql+mysqldb')
    DB_USER = os.environ['DB_USER']
    DB_PASS = os.environ['DB_PASS']
    DB_HOST = os.environ['DB_HOST']
    DB_PORT = os.environ['DB_PORT']
    DB_DATABASE = os.environ['DB_DATABASE']
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI',
        '{0}://{1}:{2}@{3}:{4}/{5}?charset=utf8mb4'.format(
            DB_API, DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_DATABASE
        )
    )
    SQLALCHEMY_ENGINE_OPTIONS = {}

    # Flask-Session settings
    SESSION_COOKIE_NAME = 'skey'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True
    SESSION_PERMANENT = True
    SESSION_USE_SIGNER = False
    SESSION_KEY_PREFIX = ''
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)

    # Atellix Catalog
    CATALOG_PROGRAM = os.environ['CATALOG_PROGRAM']
    CATALOG_SIGNER = os.environ['CATALOG_SIGNER']
    CATALOG_FEE_MINT = os.environ['CATALOG_FEE_MINT']
    CATALOG_FEE_ACCOUNT = os.environ['CATALOG_FEE_ACCOUNT']
    SOLANA_TRACKER = os.environ['SOLANA_TRACKER']
    with open(os.environ['CATALOG_SCHEMA_FILE']) as sch:
        CATALOG_SCHEMA = json.load(sch)

    # Atellix Catalog: Typesense Index
    TYPESENSE_HOST=os.environ['TYPESENSE_HOST']
    TYPESENSE_PORT=os.environ['TYPESENSE_PORT']
    TYPESENSE_PROTOCOL=os.environ['TYPESENSE_PROTOCOL']
    TYPESENSE_API_KEY=os.environ['TYPESENSE_API_KEY']

    # Atellix Catalog: OpenLink Virtuoso
    RDF_SPARQL = os.environ['RDF_SPARQL']
    RDF_CONTEXT = os.environ['RDF_CONTEXT']
    #RDF_DATABASE = os.environ['RDF_DATABASE']
    #RDF_USER = os.environ['RDF_USER']
    #RDF_PASSWORD = os.environ['RDF_PASSWORD']

    KEYCLOAK_CLIENT = os.environ['KEYCLOAK_CLIENT']
    KEYCLOAK_RS256_PUBLIC = os.environ['KEYCLOAK_RS256_PUBLIC']

class Development(Config):
    PRODUCTION = False

class Production(Config):
    PRODUCTION = True

class ConfigDict(dict):
    def from_object(self, obj):
        if isinstance(obj, str):
            obj = import_string(obj)
        for key in dir(obj):
            if key.isupper():
                self[key] = getattr(obj, key)

# Set `FLASK_CONFIG` env to 'Production' or 'Development' to set Config
flask_config = os.environ.get('FLASK_CONFIG', 'Development')

