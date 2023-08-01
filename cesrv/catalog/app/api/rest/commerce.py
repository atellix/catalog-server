import os
import json
import uuid
from functools import wraps
from rdflib import Graph, URIRef
from flask import current_app as app, session

from app.api.rest.base import BaseResource, CommandResource
from app.api import api_rest

from note.sql import *
from note.logging import *

from app.session import disable_session
from catalog_engine import CatalogEngine, sql_transaction
from catalog_engine.backend.vendure_backend import VendureBackend
from catalog_engine.catalog_cart import CatalogCart

class Commerce(CommandResource, BaseResource):
    class Commands:
        @disable_session
        def get_product(self, **data):
            log_warn('get_product: {}'.format(data))
            res = {}
            ce = CatalogEngine()
            gr, item_uuid, category_path, index = ce.get_product_by_key(data['key'], category=data.get('category', None))
            #log_warn(gr.serialize(format='turtle'))
            jsld = gr.serialize(format='json-ld')
            res['graph'] = json.loads(jsld)
            res['uuid'] = item_uuid
            res['path'] = category_path
            res['index'] = index
            res['result'] = 'ok'
            return res

        @disable_session
        def get_product_list(self, **data):
            res = {}
            ce = CatalogEngine()
            edition = data.get('edition', None)
            if edition is not None:
                gr, item_uuid = ce.get_summary_by_edition(edition)
            else:
                opts = data.get('options', {})
                limit = int(opts.get('limit', 12))
                page = int(opts.get('page', 1))
                ldata = ce.get_summary_by_category_slug(data['filters']['category'], limit, page)
                gr = ldata['graph']
                item_uuid = ldata['uuid']
                res['count'] = ldata['count']
                res['limit'] = ldata['limit']
                res['page'] = ldata['page']
            #log_warn(gr.serialize(format='turtle'))
            jsld = gr.serialize(format='json-ld')
            res['graph'] = json.loads(jsld)
            res['uuid'] = item_uuid
            res['result'] = 'ok'
            #log_warn(res)
            return res

        @disable_session
        def sync_merchant(self, **data):
            res = {}
            mrch = sql_row('user', id=2)            ### TODO: dynamic
            bkrec = sql_row('user_backend', id=1)   ### TODO: dynamic
            bkdata = json.loads(bkrec['config_data'])
            gr = Graph()
            gr.parse(data=mrch['merchant_data'], format='json-ld')
            vb = VendureBackend(gr, URIRef(mrch['merchant_uri']), bkdata['vendure_url'])
            res.update(vb.sync_merchant(root_id='1'))  ### TODO: root id to config data
            res['result'] = 'ok'
            return res

        @sql_transaction
        def get_cart(self, **data):
            log_warn('get_cart: {} session: {}'.format(data, session.sid))
            ct = CatalogCart()
            res = ct.get_cart()
            session['cart'] = res['id']
            del res['id']
            res['result'] = 'ok'
            return res

        @sql_transaction
        def add_cart_item(self, **data):
            log_warn('add_cart_item: {} session: {}'.format(data, session.sid))
            ct = CatalogCart()
            res = ct.add_cart_item(data['key'], data['quantity'])
            session['cart'] = res['id']
            del res['id']
            res['result'] = 'ok'
            return res

        @sql_transaction
        def update_cart_item(self, **data):
            log_warn('update_cart_item: {} session: {}'.format(data, session.sid))
            ct = CatalogCart()
            res = ct.update_cart_item(data['key'], data['quantity'])
            session['cart'] = res['id']
            del res['id']
            res['result'] = 'ok'
            return res

        @sql_transaction
        def remove_cart_item(self, **data):
            log_warn('remove_cart_item: {} session: {}'.format(data, session.sid))
            ct = CatalogCart()
            res = ct.remove_cart_item(data['key'])
            session['cart'] = res['id']
            del res['id']
            res['result'] = 'ok'
            return res

        @sql_transaction
        def set_shipping(self, **data):
            log_warn('set_shipping: {} session: {}'.format(data, session.sid))
            ct = CatalogCart()
            res = ct.set_shipping(data)
            session['cart'] = res['id']
            del res['id']
            res['result'] = 'ok'
            return res

        @sql_transaction
        def prepare_checkout(self, **data):
            log_warn('prepare_checkout: {} session: {}'.format(data, session.sid))
            ct = CatalogCart()
            res = ct.prepare_checkout(data)
            res['result'] = 'ok'
            return res

        @sql_transaction
        def checkout_complete(self, **data):
            log_warn('checkout_complete: {} session: {}'.format(data, session.sid))
            ct = CatalogCart()
            res = ct.checkout_complete()
            session['cart'] = res['id']
            del res['id']
            res['result'] = 'ok'
            return res

api_rest.add_resource(Commerce, '/commerce')

