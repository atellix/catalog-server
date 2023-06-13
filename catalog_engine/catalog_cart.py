import json
import uuid
import pprint
import krock32
from decimal import Decimal
from flask import current_app as app, session
from rdflib import Graph, URIRef

from note.sql import *
from catalog_engine.rdf_data import DataCoder
from catalog_engine.backend.vendure_backend import VendureBackend

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
            'cart_data': json.dumps({'backend': {}}),
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

    def get_cart_items(self, cart_id, limit=100, backend=False):
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
                'entry_key as id',
                'product_index',
                'label',
                'price',
                'quantity',
                'option_data',
                'image_url as image',
                '(price * quantity) as total',
                'backend_id',
                '(select user_backend.user_id from user_backend where user_backend.id=backend_id) as user_id',
            ],
            where = {'cart_id': cart_id},
            order = 'client_cart_item.id asc',
            limit = limit,
        )
        items = []
        mrch_key = {}
        for r in q:
            if backend:
                r['entry_key'] = r['id']
            encoder = krock32.Encoder(checksum=False)
            encoder.update(r['id'])
            r['id'] = encoder.finalize().upper() + '.' + str(r['product_index'])
            if not backend:
                del r['product_index']
            r['option_data'] = json.loads(r['option_data'])
            items.append(r)
            mrch_key.setdefault(r['user_id'], [])
            mrch_key[r['user_id']].append(r)
            del r['user_id']
        mq = nsql.table('client_cart_item').get(
            select = ['distinct u.id', 'u.merchant_uri', 'u.merchant_label', 'u.merchant_data'],
            table = 'client_cart_item ci, user_backend ub, user u',
            join = ['ci.backend_id=ub.id', 'ub.user_id=u.id'],
            where = {'ci.cart_id': cart_id},
            order = 'u.id asc',
            limit = limit,
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
        cart_data['cart_data'] = {}
        cart_data['cart_items'] = self.get_cart_items(cart_id)
        return cart_data

    def backend_add_cart_item(self, cart, backend_id, product, index, price, quantity):
        bkrec = sql_row('user_backend', id=backend_id)
        if not bkrec.exists():
            raise Exception('Invalid user backend: {}'.format(bkid))
        urec = sql_row('user', id=bkrec['user_id'])
        bkcfg = json.loads(bkrec['config_data'])
        backend = bkrec['backend_name']
        internal_data = json.loads(cart['cart_data'])
        internal_data.setdefault('backend', {})
        internal_data['backend'].setdefault(backend, {})
        internal_data['backend'][backend].setdefault(backend_id, {})
        item_data = None
        net_price = None
        tax_diff = None
        if backend == 'vendure':
            vb = VendureBackend(None, URIRef(urec['merchant_uri']), bkcfg['vendure_url'])
            if product['type'] == 'IProductGroup':
                variant_id = product['hasVariant'][index]['productID']
            else:
                variant_id = product['productID']
            res = vb.add_to_cart(variant_id, int(quantity))
            backend_data = internal_data['backend'][backend][backend_id]
            backend_data['auth'] = res['auth']
            backend_data['code'] = res['code']
            net_price = Decimal(res['net_price'])
            item_data = {
                'line': res['line'],
            }
        updates = {'cart_data': json.dumps(internal_data)}
        if item_data is not None:
            item_data = json.dumps(item_data)
        if net_price is not None:
            stnd_price = price * quantity
            if net_price != stnd_price:
                if net_price < stnd_price:
                    raise Exception('Net price less than standard price for product: {}'.format(product['id']))
                tax_diff = net_price - stnd_price
                tax_diff = str(tax_diff)
        #print('Cart Updates: {}'.format(updates))
        cart.update(updates)
        return item_data, tax_diff

    def backend_remove_cart_item(self, cart, backend_id, product, index, price, quantity):
        bkrec = sql_row('user_backend', id=backend_id)
        if not bkrec.exists():
            raise Exception('Invalid user backend: {}'.format(bkid))
        urec = sql_row('user', id=bkrec['user_id'])
        bkcfg = json.loads(bkrec['config_data'])
        backend = bkrec['backend_name']

 
    def add_cart_item(self, slug, quantity):
        qty = int(round(Decimal(quantity), 0))
        if qty <= 0:
            raise Exception('Invalid quantity')
        entry_key, index = self.decode_entry_key(slug)
        entry = sql_row('entry', entry_key=entry_key)
        if not entry.exists():
            raise Exception('Invalid entry')
        record = sql_row('record', id=entry['record_id'])
        gr = Graph()
        gr.parse(data=record['data'], format='json-ld')
        coder = DataCoder(self.obj_schema, gr, None)
        product = coder.decode_rdf(entry['external_uri'])
        cart = self.build_cart()
        cart_id = cart.sql_id()
        item = sql_row('client_cart_item', cart_id=cart_id, entry_key=entry_key, product_index=index)
        if item.exists():
            newqty = item['quantity'] + qty
            #self.backend_update_cart_item(cart, item['backend_id'], product, qty)
            item.update({
                'quantity': newqty,
            })
        else:
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
            backend_data, net_tax = self.backend_add_cart_item(cart, entry['backend_id'], product, index, price, qty)
            sql_insert('client_cart_item', {
                'cart_id': cart_id,
                'backend_id': entry['backend_id'],
                'backend_data': backend_data,
                'option_data': '{}',
                'product_index': index,
                'entry_id': entry.sql_id(),
                'entry_key': entry_key,
                'quantity': qty,
                'price': str(price),
                'net_tax': net_tax,
                'label': label,
                'image_url': img,
            })
        cart.update({
            'ts_updated': sql_now(),
        })
        cart_updated = sql_row('client_cart', id=cart_id)
        cart_data = cart_updated.data()
        cart_data['cart_data'] = {}
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
        cart.update({
            'ts_updated': sql_now(),
        })
        cart_updated = sql_row('client_cart', id=cart_id)
        cart_data = cart_updated.data()
        cart_data['cart_data'] = {}
        cart_data['cart_items'] = self.get_cart_items(cart_id)
        return cart_data
 
    def remove_cart_item(self, slug):
        entry_key, index = self.decode_entry_key(slug)
        cart = self.build_cart()
        cart_id = cart.sql_id()
        item = sql_row('client_cart_item', cart_id=cart_id, entry_key=entry_key, product_index=index)
        if item.exists():
            item.delete()
        cart.update({
            'ts_updated': sql_now(),
        })
        cart_updated = sql_row('client_cart', id=cart_id)
        cart_data = cart_updated.data()
        cart_data['cart_data'] = {}
        cart_data['cart_items'] = self.get_cart_items(cart_id)
        return cart_data

    def get_entry_product(self, entry_key):
        entry = sql_row('entry', entry_key=entry_key)
        record = sql_row('record', id=entry['record_id'])
        gr = Graph()
        gr.parse(data=record['data'], format='json-ld')
        coder = DataCoder(self.obj_schema, gr, None)
        product = coder.decode_rdf(entry['external_uri'])
        return product

    def prepare_checkout(self):
        cart = self.build_cart()
        cart_id = cart.sql_id()
        internal_data = json.loads(cart['cart_data'])
        if not internal_data.get('checkout_prepared', False):
            internal_data.setdefault('backend', {})
            items = self.get_cart_items(cart_id, limit=1000, backend=True)
            merchants = items['merchants']
            backends = {}
            for item in items['items']:
                if item['backend_id'] not in backends:
                    backends[item['backend_id']] = {
                        'products': [],
                        'merchant': merchants[item['merchant']],
                    }
                product = self.get_entry_product(item['entry_key'])
                backends[item['backend_id']]['products'].append({
                    'product': product,
                    'quantity': item['quantity'],
                    'index': item['product_index'],
                })
                del item['product_index']
                del item['backend_id']
                del item['entry_key']
            for bkid in backends.keys():
                backend_cart = backends[bkid]
                bkrec = sql_row('user_backend', id=bkid)
                if not bkrec.exists():
                    raise Exception('Invalid user backend: {}'.format(bkid))
                bkcfg = json.loads(bkrec['config_data'])
                backend = bkrec['backend_name']
                internal_data['backend'].setdefault(bkid, {})
                backend_data = internal_data['backend'][bkid]
                if backend == 'vendure':
                    vb = VendureBackend(None, URIRef(backend_cart['merchant']['id']), bkcfg['vendure_url'])
                    backend_data.update(vb.prepare_checkout(backend_cart['merchant'], backend_cart['products']))
            internal_data['checkout_prepared'] = True
            cart.update({
                'cart_data': json.dumps(internal_data),
                'ts_updated': sql_now(),
            })
            cart_items = items
        else:
            cart_items = self.get_cart_items(cart_id)
        cart_updated = sql_row('client_cart', id=cart_id)
        cart_data = cart_updated.data()
        cart_data['cart_data'] = {}
        cart_data['cart_items'] = cart_items
        return cart_data

