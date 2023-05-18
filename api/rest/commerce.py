import os
import json
import uuid
from rdflib import Graph, URIRef
from flask import current_app as app

from api.rest.base import BaseResource, CommandResource
from api import api_rest

# TODO: dynamic
VENDURE_URL = 'http://173.234.24.74:3000/shop-api'
MERCHANT_URI = 'https://savvyco.com/'

from catalog_engine import CatalogEngine
from catalog_engine.backend.vendure_backend import VendureBackend

class Commerce(CommandResource, BaseResource):
    class Commands:
        def get_product(self, **data):
            res = {}
            gr = Graph()
            with open('merchant.rdf') as f:
                gr.parse(data=f.read(), format='xml')
            vb = VendureBackend(gr, URIRef(MERCHANT_URI), VENDURE_URL)
            item_uuid = vb.build_product(data['product'])
            #print(gr.serialize(format='turtle'))
            jsld = gr.serialize(format='json-ld')
            res['graph'] = json.loads(jsld)
            res['uuid'] = item_uuid
            res['result'] = 'ok'
            return res

        def get_product_list(self, **data):
            res = {}
            gr = Graph()
            with open('merchant.rdf') as f:
                gr.parse(data=f.read(), format='xml')
            vb = VendureBackend(gr, URIRef(MERCHANT_URI), VENDURE_URL)
            item_uuid = vb.build_product_list(data['filters']['category'])
            jsld = gr.serialize(format='json-ld')
            #print(gr.serialize(format='turtle'))
            res['graph'] = json.loads(jsld)
            res['uuid'] = item_uuid
            res['result'] = 'ok'
            return res

        def get_collection_list(self, **data):
            res = {}
            gr = Graph()
            with open('merchant.rdf') as f:
                gr.parse(data=f.read(), format='xml')
            vb = VendureBackend(gr, URIRef(MERCHANT_URI), VENDURE_URL)
            item_uuid = vb.build_catalog()
            #print(gr.serialize(format='turtle'))
            jsld = gr.serialize(format='json-ld')
            res['graph'] = json.loads(jsld)
            res['uuid'] = item_uuid
            res['result'] = 'ok'
            return res

        def sync_merchant(self, **data):
            res = {}
            gr = Graph()
            with open('merchant.rdf') as f:
                gr.parse(data=f.read(), format='xml')
            vb = VendureBackend(gr, URIRef(MERCHANT_URI), VENDURE_URL)
            res.update(vb.sync_merchant(root_id='1'))
            res['result'] = 'ok'
            return res

api_rest.add_resource(Commerce, '/commerce')

