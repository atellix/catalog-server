import json
import uuid
import pprint
import krock32
from decimal import Decimal
from flask import current_app as app, session
from rdflib import Graph, URIRef

from note.sql import *
from catalog_engine.rdf_data import DataCoder

class CatalogCart():
    def __init__(self):
        with open('/home/mfrager/vend/catalog-server/object_schema.json') as f: # TODO: config
            self.obj_schema = json.load(f)

    def build_cart(self):
        if 'cart' in session:
            crc = sql_row('client_cart', id=session['cart'], checkout_cancel=0)
            if crc.exists():
                return crc
        now = sql_now()
        crc = sql_insert('client_cart', {
            'cart_data': '{}',
            'ts_created': now,
            'ts_updated': now,
            'checkout_complete': False,
            'checkout_cancel': False,
            'cart_currency': 'USD',
            'cart_subtotal': 0,
            'cart_tax': 0,
            'cart_total': 0,
        })
        return crc

    def decode_entry_key(self, slug):
        index = 0
        if '.' in slug:
            pts = slug.split('.', 2)
            slug = pts[0]
            index = int(pts[1])
        if '-' in slug:
            slug = slug.split('-')[-1]
        decoder = krock32.Decoder(strict=False, checksum=False)
        decoder.update(slug)
        entry_key = decoder.finalize()
        if len(entry_key) != 10:
            raise Exception('Invalid entry key size')
        return entry_key, index

    def get_cart_items(self, cart_id):
        ct = nsql.table('client_cart_item').get(
            select = 'count(id) as ct',
            where = {'cart_id': cart_id},
            result = list,
        )[0][0]
        tq = nsql.table('client_cart_item').get(
            select = 'sum(quantity) as ct',
            where = {'cart_id': cart_id},
            result = list,
        )[0][0]
        q = nsql.table('client_cart_item').get(
            select = [
                '(select user_backend.user_id from user_backend where user_backend.id=backend_id) as user_id',
                '(price * quantity) as total',
                'image_url as image',
                'entry_key as id',
                'product_index',
                'option_data',
                'quantity',
                'price',
                'label',
            ],
            where = {'cart_id': cart_id},
            order = 'client_cart_item.id asc',
            limit = 100,
        )
        items = []
        mrch_key = {}
        for r in q:
            encoder = krock32.Encoder(checksum=False)
            encoder.update(r['id'])
            r['id'] = encoder.finalize().upper() + '.' + str(r['product_index'])
            del r['product_index']
            r['option_data'] = json.loads(r['option_data'])
            items.append(r)
            mrch_key.setdefault(r['user_id'], [])
            mrch_key[r['user_id']].append(r)
            del r['user_id']
        mq = nsql.table('client_cart_item').get(
            select = ['u.id', 'u.merchant_uri', 'u.merchant_label', 'u.merchant_data'],
            table = 'client_cart_item ci, user_backend ub, user u',
            join = ['ci.backend_id=ub.id', 'ub.user_id=u.id'],
            where = {'ci.cart_id': cart_id},
            order = 'u.id asc',
            limit = 100,
        )
        merchants = []
        midx = 0
        for mr in mq:
            mr['index'] = midx
            merchants.append({
                'id': mr['merchant_uri'],
                'label': mr['merchant_label'],
                'data': json.loads(mr['merchant_data']),
                'index': midx,
            })
            midx = midx + 1
        for mr in mq:
            if mr['id'] in mrch_key:
                for rc in mrch_key[mr['id']]:
                    rc['merchant'] = mr['index']
        return {
            'item_count': ct,
            'item_quantity': tq,
            'items': items,
            'merchants': merchants,
        }

    def get_cart(self):
        cart = self.build_cart()
        cart_id = cart.sql_id()
        cart_updated = sql_row('client_cart', id=cart_id)
        cart_data = cart_updated.data()
        cart_data['cart_data'] = json.loads(cart_data['cart_data'])
        cart_data['cart_items'] = self.get_cart_items(cart_id)
        return cart_data
 
    def add_cart_item(self, slug, quantity):
        entry_key, index = self.decode_entry_key(slug)
        entry = sql_row('entry', entry_key=entry_key)
        if not entry.exists():
            raise Exception('Invalid entry')
        qty = int(round(Decimal(quantity), 0))
        if qty <= 0:
            raise Exception('Invalid quantity')
        cart = self.build_cart()
        cart_id = cart.sql_id()
        item = sql_row('client_cart_item', cart_id=cart_id, entry_key=entry_key, product_index=index)
        if item.exists():
            item.update({
                'quantity': item['quantity'] + qty
            })
        else:
            record = sql_row('record', id=entry['record_id'])
            gr = Graph()
            gr.parse(data=record['data'], format='json-ld')
            coder = DataCoder(self.obj_schema, gr, None)
            product = coder.decode_rdf(entry['external_uri'])
            img = None
            label = product['name']
            if 'image' in product and len(product['image']) > 0 and 'url' in product['image'][0]:
                img = product['image'][0]['url']
            if product['type'] == 'IProductGroup':
                if index >= len(product['hasVariant']):
                    raise Exception('Invalid product variant index: {}'.format(index))
                product = product['hasVariant'][index]
                # Use variant image if exists
                if 'name' in product:
                    label = product['name']
                if 'image' in product and len(product['image']) > 0 and 'url' in product['image'][0]:
                    img = product['image'][0]['url']
            offer = product['offers'][0]
            price = Decimal(offer['price'])
            sql_insert('client_cart_item', {
                'cart_id': cart_id,
                'backend_id': entry['backend_id'],
                'option_data': '{}',
                'product_index': index,
                'entry_id': entry.sql_id(),
                'entry_key': entry_key,
                'quantity': qty,
                'price': str(price),
                'label': label,
                'image_url': img,
            })
        cart_updated = sql_row('client_cart', id=cart_id)
        cart_data = cart_updated.data()
        cart_data['cart_data'] = json.loads(cart_data['cart_data'])
        cart_data['cart_items'] = self.get_cart_items(cart_id)
        return cart_data

    def update_cart_item(self, slug, quantity):
        qty = int(round(Decimal(quantity), 0))
        if qty <= 0:
            raise Exception('Invalid quantity')
        entry_key, index = self.decode_entry_key(slug)
        cart = self.build_cart()
        cart_id = cart.sql_id()
        item = sql_row('client_cart_item', cart_id=cart_id, entry_key=entry_key, product_index=index)
        if not item.exists():
            raise Exception('Invalid cart entry key: {}'.format(slug))
        item.update({
            'quantity': qty,
        })
        cart_updated = sql_row('client_cart', id=cart_id)
        cart_data = cart_updated.data()
        cart_data['cart_data'] = json.loads(cart_data['cart_data'])
        cart_data['cart_items'] = self.get_cart_items(cart_id)
        return cart_data
 
    def remove_cart_item(self, slug):
        entry_key, index = self.decode_entry_key(slug)
        cart = self.build_cart()
        cart_id = cart.sql_id()
        item = sql_row('client_cart_item', cart_id=cart_id, entry_key=entry_key, product_index=index)
        if item.exists():
            item.delete()
        cart_updated = sql_row('client_cart', id=cart_id)
        cart_data = cart_updated.data()
        cart_data['cart_data'] = json.loads(cart_data['cart_data'])
        cart_data['cart_items'] = self.get_cart_items(cart_id)
        return cart_data
 
