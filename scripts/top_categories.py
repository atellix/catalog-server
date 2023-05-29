#!/usr/bin/env python3

import os
import sys
import json
import uuid
import pprint
from sqlalchemy import create_engine
from dotenv import load_dotenv
from rdflib import Graph, URIRef
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

# Graph Database
virtuoso = SPARQLEndpoint(cfg.RDF_SPARQL)
gdb = SPARQLBackend(virtuoso, default_graph=URIRef(cfg.RDF_CONTEXT))

q = nsql.table('entry').get(
    select = [
        '(select uri from uri where uri_hash=lp.category_hash) as category_uri',
        'count(e.id) as ct',
    ],
    table = 'entry e, entry_listing el, listing_posted lp',
    join = ['el.entry_id=e.id', 'el.listing_posted_id=lp.id'],
    group = 'lp.category_hash',
    order = 'ct desc',
)
#pprint.pprint(q)

def get_products(category_uri):
    q = nsql.table('entry').get(
        select = [
            'ub.user_id',
            'ub.backend_name',
            'e.id',
        ],
        table = 'entry e, entry_listing el, listing_posted lp, uri, user_backend ub',
        join = ['el.entry_id=e.id', 'el.listing_posted_id=lp.id', 'lp.category_hash=uri.uri_hash'],
        where = {
            'uri.uri': category_uri,
        },
    )
    print(q)

if True:
    for r in q:
        curi = URIRef(r['category_uri'])
        res = gdb.get_resource(r['category_uri'])
        #print(res.serialize(format='turtle'))
        label = res.value(curi, RDFS['label'])
        if label is None:
            label = res.value(curi, SKOS['prefLabel'])
        print('{}: {}'.format(r['category_uri'], label))
        get_products(r['category_uri'])

