#!/usr/bin/env python3

import os
import sys
import json
import uuid
import pprint
import urllib.parse
from sqlalchemy import create_engine
from dotenv import load_dotenv
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD, SKOS, OWL

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

graph = Graph()

root = URIRef('http://rdf.atellix.net/1.0/catalog/public')

with open('categories_map.json') as j:
    cat_map = json.loads(j.read())

pprint.pprint(cat_map)

def make_slug(label):
    slug = label.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    return slug

slugs = {}
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
                print(f'---{mp}---')
                graph.add((node, OWL.sameAs, URIRef(mp)))

with open('public_categories.json') as j:
    json_tree = json.loads(j.read())
    create_rdf_graph(json_tree)
    graph.serialize('public_categories.ttl', format='turtle')

