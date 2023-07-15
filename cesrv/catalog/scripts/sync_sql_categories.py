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

load_dotenv('../../../.env')
sys.path.append('..')
os.environ['CATALOG_SCHEMA_FILE'] = '../object_schema.json'
from config import Config as cfg

from note.sql import *
from note.database import db, checkout_listener
from note.rdf import *
from note.rdf_database import *
from note.rdf_record import *

# MySQL Database
engine = create_engine(cfg.SQLALCHEMY_DATABASE_URI)
SQLDatabase('default', engine, dialect='mysql')

def build_internal_category(category):
    rc = sql_row('category_internal', internal_uri=category)
    if rc.exists():
        return rc
    return sql_insert('category_internal', {
        'internal_uri': category,
    })

def build_public_category(category, slug):
    rc = sql_row('category_public', public_uri=category)
    if rc.exists():
        return rc
    return sql_insert('category_public', {
        'public_uri': category,
        'slug': slug,
    })

def link_public_internal(pub_cat, int_cat):
    rc = sql_row('category_public_internal', public_id=pub_cat, internal_id=int_cat)
    if rc.exists():
        return
    sql_insert('category_public_internal', {
        'public_id': pub_cat,
        'internal_id': int_cat,
    })

def dfs(graph, node, depth=0, path=[]):
    print('  ' * depth + str(node))
    narrower_objects = graph.objects(node, SKOS['narrower'])
    slug = graph.value(node, SKOS['altLabel'])
    label = graph.value(node, RDFS['label'])
    rec = {
        'label': label,
        'slug': slug,
        'category': str(node),
        'depth': depth,
    }
    ch = []
    if slug:
        path.append({
            'key': slug,
            'name': label,
        })
    for obj in narrower_objects:
        ch.append(dfs(graph, obj, depth + 1))
    ch = sorted(ch, key=lambda c: c['label'])
    rec['children'] = ch
    internal_categories = graph.objects(node, OWL['sameAs'])
    itcs = []
    for cat in internal_categories:
        itcs.append(str(cat))
    rec['internal'] = sorted(itcs)
    if slug:
        pub_cat = build_public_category(rec['category'], slug)
        pub_cat.update({'path': json.dumps(path)})
        for intc in itcs:
            int_cat = build_internal_category(intc)
            link_public_internal(pub_cat.sql_id(), int_cat.sql_id())
        path.pop()
    return rec

gr = Graph()
gr.parse('public_categories.ttl')

root = URIRef('http://rdf.atellix.net/1.0/catalog/public')
tree = dfs(gr, root)

print(json.dumps(tree, indent=4))

