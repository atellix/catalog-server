#!/usr/bin/env python3
import json
import pprint
from rdflib import Graph, URIRef

g = Graph()
g.parse('merchant.rdf')

jsl = json.loads(g.serialize(format='json-ld'))
print(json.dumps(jsl))

