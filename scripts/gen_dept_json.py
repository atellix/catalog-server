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
#virtuoso = SPARQLEndpoint(cfg.RDF_SPARQL)
#gdb = SPARQLBackend(virtuoso, default_graph=URIRef(cfg.RDF_CONTEXT))

def count_products(intcat):
    ct = nsql.table('entry').get(
        select = [
            'count(distinct e.id) as ct',
        ],
        table = 'entry e, entry_listing el, listing_posted lp, uri',
        join = ['el.entry_id=e.id', 'el.listing_posted_id=lp.id', 'lp.category_hash=uri.uri_hash'],
        where = {
            'uri.uri': intcat,
        },
    )[0]['ct']
    #print(intcat, ct)
    return ct

def dfs(graph, node, depth=0):
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
    for obj in narrower_objects:
        ch.append(dfs(graph, obj, depth + 1))
    ch = sorted(ch, key=lambda c: c['label'])
    rec['children'] = ch
    internal_categories = graph.objects(node, OWL['sameAs'])
    itcs = []
    for cat in internal_categories:
        itcs.append(str(cat))
    rec['internal'] = itcs
    prc = 0
    for item in itcs:
        prc = prc + count_products(item)
    rec['products'] = prc
    return rec

gr = Graph()
gr.parse('public_categories.ttl')

root = URIRef('http://rdf.atellix.net/1.0/catalog/public')
tree = dfs(gr, root)

#print(json.dumps(tree, indent=4))

slugs = {}
menu = []
for top in tree['children']:
    mi = {
        'title': top['label'],
    }
    slugs[top['slug']] = top['category']
    if top['products'] > 0:
        mi['url'] = '/shop/catalog/' + top['slug']
    menu.append(mi)
    if len(top['children']):
        submenu = []
        mi['submenu'] = {
            'type': 'menu',
            'menu': submenu,
        }
        for nl in top['children']:
            ms = {
                'title': nl['label'],
            }
            slugs[nl['slug']] = nl['category']
            if nl['products'] > 0:
                ms['url'] = '/shop/catalog/' + nl['slug']
            submenu.append(ms)
    
with open('headerDepartments.json', 'w') as f:
    f.write(json.dumps(menu, indent=4))

with open('categories_slugs.json', 'w') as f:
    f.write(json.dumps(slugs, indent=4))

