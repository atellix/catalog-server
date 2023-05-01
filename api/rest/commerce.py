import os
import json
import uuid
from rdflib import Graph, URIRef
from flask import current_app as app

from api.rest.base import BaseResource, CommandResource
from api import api_rest

# TODO: dynamic
VENDURE_URL = 'http://173.234.24.74:3000/shop-api'

class Commerce(CommandResource, BaseResource):
    class Commands:
        def get_product(self, **data):
            res = {}
            gr = Graph()
            with open('merchant.rdf') as f:
                gr.parse(data=f.read(), format='xml')
            vb = VendureBackend(URIRef('https://savvyco.com/'), VENDURE_URL)
            item_uuid = vb.build_product(gr, product_id)
            #print(gr.serialize(format='turtle'))
            jsld = gr.serialize(format='json-ld')
            res['graph'] = json.loads(jsld)
            res['uuid'] = item_uuid
            res['result'] = 'ok'
            return res

        def get_collection_list(self, **data):
            res = {}
            gr = Graph()
            vb = VendureBackend(URIRef('https://savvyco.com/'), VENDURE_URL)
            item_uuid = vb.build_catalog(gr)
            #print(gr.serialize(format='turtle'))
            jsld = gr.serialize(format='json-ld')
            res['graph'] = json.loads(jsld)
            res['uuid'] = item_uuid
            res['result'] = 'ok'
            return res

#        def get_collection(self, **data):
#            res = {}
#            res['result'] = 'ok'
#            return res

api_rest.add_resource(Commerce, '/commerce')

