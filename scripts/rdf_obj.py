#!/usr/bin/env python3
import json
import pprint
from rdflib import Graph, URIRef
from catalog_engine.rdf_data import DataCoder

with open('object_schema.json') as f:
    schema = json.load(f)

gr = Graph()
dc = DataCoder(schema, gr, 'http://rdf.atellix.net/uuid')

spec = dc.encode_rdf({
    'id': 'http://some.thing/1',
    'type': 'IProduct',
    'name': 'Hello World',
    'image': [
        {'url': 'https://images.com/123.jpg'},
        {'url': 'https://images.com/456.jpg'},
        {'url': 'https://images.com/789.jpg'},
    ],
    'offers': [{
        'price': '100.12',
        'priceCurrency': 'USD',
    }],
})

#print(spec[0])
print(gr.serialize(format='turtle'))

pprint.pprint(dc.decode_rdf(spec[0]))
