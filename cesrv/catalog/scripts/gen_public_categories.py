#!/usr/bin/env python3

import re
import os
import sys
import json
import uuid
import pprint
import urllib.parse
from dotenv import load_dotenv
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD, SKOS, OWL

graph = Graph()
slugs = {}
root = URIRef('http://rdf.atellix.net/1.0/catalog/public')
with open('categories_map.json') as j:
    cat_map = json.loads(j.read())

#pprint.pprint(cat_map)

def make_slug(label):
    slug = label.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    return slug

def create_rdf_graph(data, parent_node=None):
    for key, value in data.items():
        # Create a new node for the current key
        node = URIRef('http://rdf.atellix.net/1.0/catalog/public/' + urllib.parse.quote(key))
        graph.add((node, RDF.type, SKOS.Concept))
        graph.add((node, RDFS.label, Literal(key)))
        slug = make_slug(key)
        if slug in slugs:
            raise Exception('Duplicate slug: {}'.format(slug))
        slugs[slug] = True
        graph.add((node, SKOS.altLabel, Literal(slug)))

        if parent_node:
            # Link the current node to its parent
            graph.add((node, SKOS.broader, parent_node))
            graph.add((parent_node, SKOS.narrower, node))
        else:
            graph.add((node, SKOS.broader, root))
            graph.add((root, SKOS.narrower, node))

        if isinstance(value, dict):
            # If the value is a dictionary, recursively call the function
            create_rdf_graph(value, node)
        else:
            # Otherwise, it's a leaf node
            graph.add((node, RDF.type, SKOS.Concept))

        if str(node) in cat_map:
            for mp in cat_map[str(node)].keys():
                graph.add((node, OWL.sameAs, URIRef(mp)))
        else:
            cat_map[str(node)] = {}

with open('public_categories.json') as j:
    json_tree = json.load(j)
    create_rdf_graph(json_tree)
    graph.serialize('public_categories.ttl', format='turtle')

if True:
    with open('categories_map.json', 'w') as m:
        m.write(json.dumps(cat_map, indent=4, sort_keys=True))

