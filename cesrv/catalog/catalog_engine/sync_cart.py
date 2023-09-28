import uuid
import json
import requests
from decimal import Decimal
from flask import current_app as app
from rdflib import Graph, URIRef

from note.sql import * 
from note.logging import *
from catalog_engine.rdf_data import DataCoder
from .sync_data import DataSync

class SyncCart(DataSync):
    def __init__(self, catalog_cart, cart, backend_id):
        self.catalog_cart = catalog_cart
        self.cart = cart
        self.backend_id = backend_id
        self.backend = sql_row('user_backend', id=backend_id)
        self.cart_backend = sql_row('client_cart_backend', cart_id=cart.sql_id(), backend_id=backend_id)
        self.update = True
        self.src_data = {}
        self.dst_data = {}

    def load(self):
        user = sql_row('user', id=self.backend['user_id'])
        user_id = user.sql_id()
        if not(user['active']):
            return
        #log_warn('Cart Sync: {}'.format(self.backend.data()))
        # Get destination data
        items = nsql.table('client_cart_item').get(
            select = ['ci.id', 'ci.price', 'ci.price', 'ci.product_index', 'ci.quantity', 'ci.entry_key', 'e.external_id'],
            table = 'client_cart_item ci, entry e',
            join = ['ci.entry_key=e.entry_key'],
            where = {
                'ci.cart_id': self.cart.sql_id(),
                'ci.backend_id': self.backend_id,
            },
        )
        for r in items:
            #log_warn(r)
            r['quantity'] = int(r['quantity'])
            self.src_data[str(r['external_id'])] = r
        backend_data = json.loads(self.cart_backend['backend_data'])
        if 'cart' in backend_data:
            #log_warn(backend_data)
            self.dst_data = backend_data['cart']

    def src_items(self):
        return self.src_data.keys()

    def src_has(self, item):
        res = item in self.src_data
        return res

    def dst_items(self):
        return self.dst_data.keys()

    def dst_has(self, item):
        res = item in self.dst_data
        return res

    def dst_add(self, item):
        log_warn('Cart Add {}'.format(item))
        add_item = self.src_data[item]
        index = add_item['product_index']
        price = Decimal(add_item['price'])
        quantity = int(add_item['quantity'])
        cart_item = {'external_id': add_item['external_id'], 'id': add_item['id'], 'quantity': quantity}
        entry = sql_row('entry', entry_key=add_item['entry_key'])
        if not entry.exists():
            raise Exception('Invalid entry')
        gr = Graph()
        gr.parse(data=entry['data_jsonld'], format='json-ld')
        coder = DataCoder(self.catalog_cart.obj_schema, gr, None)
        product = coder.decode_rdf(entry['external_uri'])
        item_data, net_tax = self.catalog_cart.backend_add_cart_item(self.cart, self.backend_id, product, index, price, quantity)
        cart_item['external_data'] = json.loads(item_data)
        itemrc = sql_row('client_cart_item', id=add_item['id'])
        if net_tax != itemrc['net_tax']:
            itemrc.update({'net_tax': net_tax})
        itemrc.update({'backend_data': item_data})
        self.cart_backend.reload()
        backend_data = json.loads(self.cart_backend['backend_data'])
        backend_data.setdefault('cart', {})
        backend_data['cart'][str(add_item['external_id'])] = cart_item
        for k in ['payments', 'payments_cache']:
            if k in backend_data:
                del backend_data[k]
        self.cart_backend.update({'backend_data': json.dumps(backend_data)})

    def dst_delete(self, item):
        log_warn('Cart Delete {}'.format(item))
        del_item = self.dst_data[item]
        backend_data = json.loads(self.cart_backend['backend_data'])
        item_data = backend_data['cart'][str(del_item['external_id'])]['external_data']
        self.catalog_cart.backend_remove_cart_item(self.cart, self.backend_id, item_data)
        self.cart_backend.reload()
        del backend_data['cart'][str(del_item['external_id'])]
        for k in ['payments', 'payments_cache']:
            if k in backend_data:
                del backend_data[k]
        self.cart_backend.update({'backend_data': json.dumps(backend_data)})

    # Returns: has_update, original_item, new_item
    def dst_eq(self, item):
        orig_item = self.dst_data[item]
        new_item = self.src_data[item]
        if orig_item['quantity'] != new_item['quantity']:
            return True, orig_item, new_item
        return False, None, None

    def dst_update(self, item, orig_item, inp):
        log_warn('Cart Update {}'.format(item))
        upd_item = self.dst_data[item]
        newqty = inp['quantity']
        backend_data = json.loads(self.cart_backend['backend_data'])
        cart_item = sql_row('client_cart_item', id=upd_item['id'])
        net_tax =self.catalog_cart.backend_update_cart_item(self.cart, self.backend_id, backend_data, cart_item, newqty)
        if net_tax != cart_item['net_tax']:
            cart_item.update({'net_tax': net_tax, 'quantity': newqty})
        else:
            cart_item.update({'quantity': newqty})
        self.cart_backend.reload()
        backend_data = json.loads(self.cart_backend['backend_data'])
        backend_data['cart'][str(upd_item['external_id'])]['quantity'] = newqty
        for k in ['payments', 'payments_cache']:
            if k in backend_data:
                del backend_data[k]
        self.cart_backend.update({'backend_data': json.dumps(backend_data)})

