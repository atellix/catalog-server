import os
import json
import uuid
from functools import wraps
from rdflib import Graph, URIRef
from flask import current_app as app, session

from api.rest.base import BaseResource, CommandResource
from api import api_rest

# TODO: dynamic
VENDURE_URL = 'http://173.234.24.74:3000/shop-api'
MERCHANT_URI = 'https://savvyco.com/'

from session import disable_session
from catalog_engine import CatalogEngine
from catalog_engine.backend.vendure_backend import VendureBackend

class Commerce(CommandResource, BaseResource):
    class Commands:
        @disable_session
        def get_product(self, **data):
            print('get_product: {}'.format(data))
            res = {}
            ce = CatalogEngine()
            gr, item_uuid, category_path = ce.get_product_by_key(data['key'], category=data.get('category', None))
            #print(gr.serialize(format='turtle'))
            jsld = gr.serialize(format='json-ld')
            res['graph'] = json.loads(jsld)
            res['uuid'] = item_uuid
            res['path'] = category_path
            res['result'] = 'ok'
            return res

        @disable_session
        def get_product_list(self, **data):
            res = {}
            ce = CatalogEngine()
            gr, item_uuid = ce.get_summary_by_category_slug(data['filters']['category'])
            #print(gr.serialize(format='turtle'))
            jsld = gr.serialize(format='json-ld')
            res['graph'] = json.loads(jsld)
            res['uuid'] = item_uuid
            res['result'] = 'ok'
            #print(res)
            return res

        @disable_session
        def get_collection_list(self, **data):
            res = {}
            gr = Graph()
            with open('merchant.rdf') as f:
                gr.parse(data=f.read(), format='xml')
            vb = VendureBackend(gr, URIRef(MERCHANT_URI), VENDURE_URL)
            item_uuid = vb.build_catalog()
            jsld = gr.serialize(format='json-ld')
            res['graph'] = json.loads(jsld)
            res['uuid'] = item_uuid
            res['result'] = 'ok'
            return res

        @disable_session
        def sync_merchant(self, **data):
            res = {}
            gr = Graph()
            with open('merchant.rdf') as f:
                gr.parse(data=f.read(), format='xml')
            vb = VendureBackend(gr, URIRef(MERCHANT_URI), VENDURE_URL)
            res.update(vb.sync_merchant(root_id='1'))
            res['result'] = 'ok'
            return res

        def get_cart(self, **data):
            print('get_cart: {}'.format(session))
            res = {}
            res['result'] = 'ok'
            return res

        def add_cart_item(self, **data):
            print('add_cart_item: {}'.format(data))
            print('session: {}'.format(session.sid))
            session.setdefault('cart', 0)
            session['cart'] = session['cart'] + 1
            print(session)
            res = {}
            res[app.session_cookie_name] = session.sid
            res['result'] = 'ok'
            return res

api_rest.add_resource(Commerce, '/commerce')

