#!/usr/bin/env python3
import sys
sys.path.append('..')

import json
import pprint
import based58
import canonicaljson
from blake3 import blake3
from rdflib import Graph, URIRef
from catalog_engine.rdf_data import DataCoder

with open('../object_schema.json') as f:
    schema = json.load(f)

gr = Graph()
uu_id = '6c6205bb-58c6-48f8-a19c-b19cf71c026a'
rec = {
    'id': 'http://some.thing/id/' + uu_id,
    #'uuid': uu_id,
    'type': 'IProduct',
    'name': 'Hello World!',
    'slug': 'Slug!',
    'image': [
        {'url': 'https://images.com/123.jpg'},
        {'url': 'https://images.com/456.jpg'},
        {'url': 'https://images.com/789.jpg'},
    ],
    'offers': [{
        'price': '100.12',
        'priceCurrency': 'USD',
    }],
}
dc = DataCoder(schema, gr, rec['id'])
spec = dc.encode_rdf(rec)
print(spec)

#print(spec[0])
print(gr.serialize(format='turtle'))

pprint.pprint(dc.decode_rdf(spec[0]))
cjs = canonicaljson.encode_canonical_json(dc.decode_rdf(spec[0]))

hs = blake3()
hs.update(cjs)
dg = hs.digest()
print(based58.b58encode(dg).decode('utf8'))
