#!/usr/bin/env python3
import json
from rdflib import Graph, URIRef
from catalog_engine.rdf_data import DataCoder

with open('object_schema.json') as f:
    schema = json.load(f)

gr = Graph()
dc = DataCoder(schema, gr, 'http://base.uri/abc')

dc.encode_rdf({
    'type': 'IEvent',
    'name': 'Hello World',
    'url': 'https://solana.com/breakpoint',
    'keywords': ['solana', 'blockchain', 'cryptocurrency', 'crypto'],
    'organizer': [{
        'type': 'IOrganization',
        'name': 'Solana Foundation',
        'sameAs': [
            { 'id': 'https://www.youtube.com/SolanaFndn' },
            { 'id': 'https://twitter.com/solana' },
            { 'id': 'https://discord.com/invite/kBbATFA7PW' },
            { 'id': 'https://www.reddit.com/r/solana' },
            { 'id': 'https://github.com/solana-labs' },
            { 'id': 'https://t.me/solana' },
        ],
    }],
})

print(gr.serialize(format='turtle'))
