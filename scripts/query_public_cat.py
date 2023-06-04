#!/usr/bin/env python3

import os
import sys
import json
import uuid
import pprint
from blake3 import blake3
from dotenv import load_dotenv
from rdflib import Graph, URIRef
from sqlalchemy import create_engine
from rdflib.namespace import RDF, RDFS, XSD, SKOS

load_dotenv('../.env')
sys.path.append('..')
from config import Config as cfg

from note.sql import *
from note.database import db, checkout_listener
from note.rdf import *
from note.rdf_database import *
from note.rdf_record import *

# MySQL Database
engine = create_engine(cfg.SQLALCHEMY_DATABASE_URI)
SQLDatabase('default', engine, dialect='mysql')

slug = 'photography'

q = nsql.table('category_internal').get(
    select = [
        'ci.internal_uri',
    ],
    table = 'category_internal ci, category_public cp, category_public_internal cpi',
    join = ['ci.id=cpi.internal_id', 'cp.id=cpi.public_id'],
    where = {
        'cp.slug': slug,
    },
)
print(q)

hash1 = blake3(b"foobarbaz").digest()
print(len(hash1))

