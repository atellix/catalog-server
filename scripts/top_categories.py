#!/usr/bin/env python3

import os
import sys
import json
import uuid
import pprint
from sqlalchemy import create_engine
from dotenv import load_dotenv
from rdflib import Graph, URIRef, Namespace
from rdflib.namespace import RDF, RDFS, XSD, SKOS

load_dotenv('../.env')
sys.path.append('..')
from config import Config as cfg

from note.sql import *
from note.database import db, checkout_listener
from note.rdf import *
from note.rdf_database import *
from note.rdf_record import *

from catalog_engine import CatalogEngine
from catalog_engine.backend.vendure_backend import VendureBackend

VENDURE_URL = 'http://173.234.24.74:3000/shop-api'
MERCHANT_URI = 'https://savvyco.com/'

SCH = Namespace('http://schema.org/')
ATX = Namespace('http://rdf.atellix.net/1.0/schema/catalog/')

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
            'e.external_id',
            'e.id',
        ],
        table = 'entry e, entry_listing el, listing_posted lp, uri, user_backend ub',
        join = ['el.entry_id=e.id', 'el.listing_posted_id=lp.id', 'lp.category_hash=uri.uri_hash'],
        where = {
            'uri.uri': category_uri,
        },
    )
    #print(q)
    for r in q:
        #print(r)
        gr = Graph()
        vb = VendureBackend(gr, URIRef(MERCHANT_URI), VENDURE_URL)
        item_uuid = vb.build_product(r['external_id'])
        uuid_uri = URIRef('urn:uuid:' + item_uuid)
        for s, p, o in gr.triples((None, ATX['Object.uuid'], uuid_uri)):
            item_uri = s
            break
        #print(gr.serialize(format='turtle'))
        name = gr.value(item_uri, SCH['name'])
        print(name)

for r in q:
    curi = URIRef(r['category_uri'])
    res = gdb.get_resource(r['category_uri'])
    #print(res.serialize(format='turtle'))
    label = res.value(curi, RDFS['label'])
    if label is None:
        label = res.value(curi, SKOS['prefLabel'])
    print(r['category_uri'])
    #print('{}: {}'.format(r['category_uri'], label))
    #get_products(r['category_uri'])

