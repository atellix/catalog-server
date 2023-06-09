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
        sess = sql_row('client_session', session_id=session.sid)
        if not(sess.exists()):
            raise Exception('Invalid session: {}'.format(session.sid))
        crc = sql_row('client_cart', session_id=sess.sql_id(), checkout_cancel=0)
        if crc.exists():
            return crc
        now = sql_now()
        crc = sql_insert('client_cart', {
            'session_id': sess.sql_id(),
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
        index = None
        if '.' in slug:
            pts = slug.split('.', 2)
            slug = pts[0]
            index = pts[1]
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
        q = nsql.table('client_cart_item').get(
            select = [
                'entry_key as id',
                'product_index',
                'option_data',
                'quantity',
                'price',
            ],
            where = {'cart_id': cart_id},
            order = 'id',
            limit = 100,
        )
        items = []
        for r in q:
            encoder = krock32.Encoder(checksum=False)
            encoder.update(r['id'])
            r['id'] = encoder.finalize().upper()
            if r['product_index']:
                r['id'] = r['id'] + '.' + str(r['product_index'])
            del r['product_index']
            r['option_data'] = json.loads(r['option_data'])
            items.append(r)
        return {
            'item_count': ct,
            'items': items,
        }

    def add_cart_item(self, slug, quantity):
        entry_key, index = self.decode_entry_key(slug)
        entry = sql_row('entry', entry_key=entry_key)
        if not entry.exists():
            raise Exception('Invalid entry')
        cart = self.build_cart()
        cart_id = cart.sql_id()
        item = sql_row('client_cart_item', cart_id=cart_id, entry_key=entry_key)
        if item.exists():
            qty = item['quantity']
            new_qty = Decimal(qty) + Decimal(quantity)
            item.update({
                'quantity': str(new_qty),
            })
        else:
            record = sql_row('record', id=entry['record_id'])
            gr = Graph()
            gr.parse(data=record['data'], format='json-ld')
            coder = DataCoder(self.obj_schema, gr, None)
            product = coder.decode_rdf(entry['external_uri'])
            if product['type'] == 'IProductGroup':
                if index is None:
                    index = 0
                else:
                    index = int(index)
                if index >= len(product['hasVariant']):
                    raise Exception('Invalid product variant index: {}'.format(index))
                product = product['hasVariant'][index]
            offer = product['offers'][0]
            price = Decimal(offer['price'])
            qty = Decimal(quantity)
            sql_insert('client_cart_item', {
                'cart_id': cart_id,
                'option_data': '{}',
                'product_index': index,
                'entry_id': entry.sql_id(),
                'entry_key': entry_key,
                'quantity': str(qty),
                'price': str(price),
            })
        cart_updated = sql_row('client_cart', id=cart_id)
        cart_data = cart_updated.data()
        cart_data['cart_data'] = json.loads(cart_data['cart_data'])
        cart_data['cart_items'] = self.get_cart_items(cart_id)
        return cart_data

