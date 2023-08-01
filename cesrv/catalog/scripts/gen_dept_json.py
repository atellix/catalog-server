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

from catalog_engine.rdf_data import DataCoder

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

with open('../object_schema.json') as f:
    obj_schema = json.load(f)

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

def get_category_id(pubcat):
    rc = sql_row('category_public', public_uri=pubcat)
    return rc.sql_id()

image_seen = {}
def get_category_image(pubcat, offset=0):
    rc = sql_row('category_public', public_uri=pubcat)
    q = nsql.table('category_public').get(
        select = [
            'e.data_summary', 'e.external_uri',
        ],
        table = 'category_public cp, entry_category ec, entry e',
        join = ['cp.id=ec.public_id', 'ec.entry_id=e.id'],
        where = {'cp.public_uri': pubcat},
        order = 'e.id asc',
        limit = 1,
        offset = offset,
        result = list,
    )
    if len(q):
        tq = q[0]
        gr = Graph()
        gr.parse(data=tq['data_summary'], format='json-ld')
        coder = DataCoder(obj_schema, gr, None)
        product = coder.decode_rdf(tq['external_uri'])
        img = product['image'][0]['url']
        if img in image_seen:
            return get_category_image(pubcat, offset + 1)
        image_seen[img] = True
        return img
    return ''

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
        mi['url'] = '/category/' + top['slug']
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
                ms['url'] = '/category/' + nl['slug']
            submenu.append(ms)

blocks = []
for top in tree['children']:
    bl = {
        'type': 'shop',
        'id': get_category_id(top['category']),
        'name': top['label'],
        'slug': top['slug'],
        'items': top['products'],
        'image': get_category_image(top['category']),
        'customFields': {},
        'children': [],
    }
    if not(len(bl['image'])) and len(top['children']):
        for nl in top['children']:
            subimg = get_category_image(nl['category'])
            if len(subimg):
                bl['image'] = subimg
                break
    blocks.append(bl)
    for nl in top['children']:
        sb = {
            'type': 'shop',
            'id': get_category_id(nl['category']),
            'slug': nl['slug'],
            'name': nl['label'],
            'customFields': {},
        }
        bl['children'].append(sb)
blocks = blocks[:6]
     
with open('headerDepartments.json', 'w') as f:
    f.write(json.dumps(menu, indent=4))

with open('categories_slugs.json', 'w') as f:
    f.write(json.dumps(slugs, indent=4))

with open('shopBlockCategories.json', 'w') as f:
    f.write(json.dumps(blocks, indent=4))

