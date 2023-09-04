import json
import uuid
import pprint
import krock32
import requests
from decimal import Decimal
from urllib.parse import urlparse
from flask import current_app as app, session
from rdflib import Graph, URIRef

from note.sql import *
from note.logging import *
from catalog_engine.rdf_data import DataCoder
from catalog_engine.backend.vendure_backend import VendureBackend

class CatalogCart():
    def __init__(self):
        self.obj_schema = app.config['CATALOG_SCHEMA']

    def build_cart(self, new_cart=False):
        if 'cart' in session and not(new_cart):
            crc = sql_row('client_cart', id=session['cart'], checkout_cancel=False, checkout_complete=False)
            if crc.exists():
                log_warn('Found cart: {} for {}'.format(crc.data(), session.sid))
                return crc
        now = sql_now()
        crc = sql_insert('client_cart', {
            'cart_data': json.dumps({'backend': {}}),
            'ts_created': now,
            'ts_updated': now,
            'checkout_complete': False,
            'checkout_prepared': False,
            'checkout_cancel': False,
            'cart_currency': 'USD',
            'cart_subtotal': 0,
            'cart_shipping': 0,
            'cart_tax': 0,
            'cart_total': 0,
        })
        log_warn('New cart: {} for {}'.format(crc.sql_id(), session.sid))
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

    def get_cart_items(self, cart_id, limit=100):
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
                'net_tax',
                'backend_id',
                'option_data',
                'image_url as image',
                '(price * quantity) as total',
                '(select user_backend.user_id from user_backend where user_backend.id=backend_id) as user_id',
            ],
            where = {'cart_id': cart_id},
            order = 'client_cart_item.id asc',
            limit = limit,
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

    def get_cart_backends(self, cart_id):
        q = nsql.table('client_cart_item').get(
            select = ['distinct backend_id'],
            where = {'cart_id': cart_id},
            order = 'client_cart_item.backend_id asc',
        )
        res = []
        for r in q:
            res.append(r['backend_id'])
        return res

    def get_cart(self):
        cart = self.build_cart()
        cart_id = cart.sql_id()
        cart_updated = sql_row('client_cart', id=cart_id)
        cart_data = cart_updated.data()
        cart_data['cart_data'] = {}
        cart_data['cart_items'] = self.get_cart_items(cart_id)
        return cart_data

    def get_backend_record(self, cart_id, backend_id):
        nrc = sql_row('client_cart_backend', cart_id=cart_id, backend_id=backend_id)
        if nrc.exists():
            return nrc
        nsql.begin()
        try:
            nrc = sql_insert('client_cart_backend', {
                'cart_id': cart_id,
                'backend_id': backend_id,
                'backend_data': '{}',
            })
            nsql.commit()
            return nrc
        except Exception as e:
            nsql.rollback()
        nrc = sql_row('client_cart_backend', cart_id=cart_id, backend_id=backend_id)
        if nrc.exists():
            return nrc
        raise Exception('Unable to create backend record for cart id: {} backend id: {}'.format(cart_id, backend_id))

    def backend_add_cart_item(self, cart, backend_id, product, index, price, quantity):
        bkrec = sql_row('user_backend', id=backend_id)
        if not bkrec.exists():
            raise Exception('Invalid user backend: {}'.format(bkid))
        urec = sql_row('user', id=bkrec['user_id'])
        bkcfg = json.loads(bkrec['config_data'])
        backend = bkrec['backend_name']
        backend_rc = self.get_backend_record(cart.sql_id(), backend_id)
        item_data = None
        net_price = None
        tax_diff = None
        if backend == 'vendure':
            vb = VendureBackend(backend_id, None, URIRef(urec['merchant_uri']), bkcfg['vendure_url'])
            backend_rc.reload()
            internal_data = json.loads(backend_rc['backend_data'])
            if 'auth' in internal_data:
                vb.set_auth_token(internal_data['auth'])
            if product['type'] == 'IProductGroup':
                variant_id = product['hasVariant'][index]['productID']
            else:
                variant_id = product['productID']
            res = vb.add_to_cart(variant_id, int(quantity))
            internal_data['auth'] = res['auth']
            internal_data['code'] = res['code']
            net_price = Decimal(res['net_price'])
            item_data = {
                'line': res['line'],
            }
            backend_rc.update({'backend_data': json.dumps(internal_data)})
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
        return item_data, tax_diff

    def backend_update_cart_item(self, cart, backend_id, cart_item, quantity):
        bkrec = sql_row('user_backend', id=backend_id)
        if not bkrec.exists():
            raise Exception('Invalid user backend: {}'.format(bkid))
        urec = sql_row('user', id=bkrec['user_id'])
        bkcfg = json.loads(bkrec['config_data'])
        backend = bkrec['backend_name']
        backend_rc = self.get_backend_record(cart.sql_id(), backend_id)
        net_price = None
        tax_diff = None
        if backend == 'vendure':
            backend_data = json.loads(backend_rc['backend_data'])
            vb = VendureBackend(backend_id, None, URIRef(urec['merchant_uri']), bkcfg['vendure_url'])
            vb.set_auth_token(backend_data['auth'])
            item_data = json.loads(cart_item['backend_data'])
            res = vb.update_cart(item_data['line'], int(quantity))
            net_price = Decimal(res['net_price'])
            if backend_data['auth'] != res['auth']:
                backend_data['auth'] = res['auth']
                backend_rc.update({'backend_data': json.dumps(backend_data)})
        if net_price is not None:
            stnd_price = Decimal(cart_item['price']) * Decimal(quantity)
            print(f'Standard Price: {stnd_price} Net Price: {net_price}')
            if net_price != stnd_price:
                if net_price < stnd_price:
                    raise Exception('Net price less than standard price for cart item: {}'.format(cart_item.sql_id()))
                tax_diff = net_price - stnd_price
                tax_diff = str(tax_diff)
        #print('Cart Updates: {}'.format(updates))
        return tax_diff

    def backend_remove_cart_item(self, cart, backend_id, cart_item):
        bkrec = sql_row('user_backend', id=backend_id)
        if not bkrec.exists():
            raise Exception('Invalid user backend: {}'.format(bkid))
        urec = sql_row('user', id=bkrec['user_id'])
        bkcfg = json.loads(bkrec['config_data'])
        backend = bkrec['backend_name']
        backend_rc = self.get_backend_record(cart.sql_id(), backend_id)
        #pprint.pprint(internal_data)
        if backend == 'vendure':
            backend_data = json.loads(backend_rc['backend_data'])
            vb = VendureBackend(backend_id, None, URIRef(urec['merchant_uri']), bkcfg['vendure_url'])
            vb.set_auth_token(backend_data['auth'])
            item_data = json.loads(cart_item['backend_data'])
            res = vb.remove_from_cart(item_data['line'])
            if backend_data['auth'] != res['auth']:
                backend_data['auth'] = res['auth']
                backend_rc.update({'backend_data': json.dumps(backend_data)})
 
    def backend_set_shipping(self, cart, backend_id, spec):
        bkrec = sql_row('user_backend', id=backend_id)
        if not bkrec.exists():
            raise Exception('Invalid user backend: {}'.format(bkid))
        urec = sql_row('user', id=bkrec['user_id'])
        bkcfg = json.loads(bkrec['config_data'])
        backend = bkrec['backend_name']
        backend_rc = self.get_backend_record(cart.sql_id(), backend_id)
        #pprint.pprint(internal_data)
        if backend == 'vendure':
            backend_data = json.loads(backend_rc['backend_data'])
            if 'shipping' in backend_data:
                ship_info = backend_data['shipping']
            else:
                vb = VendureBackend(backend_id, None, URIRef(urec['merchant_uri']), bkcfg['vendure_url'])
                vb.set_auth_token(backend_data['auth'])
                ship_methods = vb.get_shipping() # TODO: customize
                ship_info = vb.set_shipping(ship_methods[0]['id'], spec)
                backend_data['shipping'] = {
                    'price': str(ship_info['price']),
                    'tax': str(ship_info['tax']),
                }
                if backend_data['auth'] != ship_info['auth']:
                    backend_data['auth'] = ship_info['auth']
                backend_rc.update({'backend_data': json.dumps(backend_data)})
            return Decimal(ship_info['price']), Decimal(ship_info['tax'])
        raise Exception(f'Unknown backend: {backend}')
 
    def add_cart_item(self, slug, quantity):
        qty = int(round(Decimal(quantity), 0))
        if qty <= 0:
            raise Exception('Invalid quantity')
        entry_key, index = self.decode_entry_key(slug)
        entry = sql_row('entry', entry_key=entry_key)
        if not entry.exists():
            raise Exception('Invalid entry')
        gr = Graph()
        gr.parse(data=entry['data_jsonld'], format='json-ld')
        coder = DataCoder(self.obj_schema, gr, None)
        product = coder.decode_rdf(entry['external_uri'])
        cart = self.build_cart()
        cart_id = cart.sql_id()
        item = sql_row('client_cart_item', cart_id=cart_id, entry_key=entry_key, product_index=index)
        if item.exists():
            newqty = item['quantity'] + qty
            net_tax = self.backend_update_cart_item(cart, str(entry['backend_id']), item, newqty)
            item.update({
                'quantity': newqty,
                'net_tax': net_tax,
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
            backend_data, net_tax = self.backend_add_cart_item(cart, str(entry['backend_id']), product, index, price, qty)
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
        entry = sql_row('entry', entry_key=item['entry_key'])
        if not entry.exists():
            raise Exception('Invalid entry')
        net_tax = self.backend_update_cart_item(cart, str(entry['backend_id']), item, qty)
        item.update({
            'quantity': qty,
            'net_tax': net_tax,
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
            entry = sql_row('entry', entry_key=item['entry_key'])
            if not entry.exists():
                raise Exception('Invalid entry')
            self.backend_remove_cart_item(cart, str(entry['backend_id']), item)
            item.delete()
        cart.update({
            'ts_updated': sql_now(),
        })
        cart_updated = sql_row('client_cart', id=cart_id)
        cart_data = cart_updated.data()
        cart_data['cart_data'] = {}
        cart_data['cart_items'] = self.get_cart_items(cart_id)
        return cart_data

    def set_shipping(self, spec):
        cart = self.build_cart()
        cart_id = cart.sql_id()
        backends = self.get_cart_backends(cart_id)
        for bkid in backends:
            ship_price, ship_tax = self.backend_set_shipping(cart, str(bkid), spec)
            src = sql_row('client_cart_shipping', cart_id=cart_id, backend_id=bkid)
            if src.exists():
                src.update({
                    'shipping_price': str(ship_price),
                    'shipping_tax': str(ship_tax),
                })
            else:
                sql_insert('client_cart_shipping', {
                    'cart_id': cart_id,
                    'backend_id': bkid,
                    'shipping_price': str(ship_price),
                    'shipping_tax': str(ship_tax),
                })
        cart_updated = sql_row('client_cart', id=cart_id)
        cart_data = cart_updated.data()
        cart_data['cart_data'] = {}
        cart_data['cart_items'] = self.get_cart_items(cart_id)
        return cart_data

    def request_payment(self, vendure_url, payment_method, amount, order_code):
        if not(payment_method == 'atellixpay' or payment_method == 'authorizenet'):
            raise Exception('Invalid payment method: {}'.format(payment_method))
        pts = urlparse(vendure_url)
        url = 'https://{}/payments/{}'.format(pts.hostname, payment_method)
        rq = requests.post(url, data={'event': 'payment_request', 'amount': amount, 'order_id': order_code})
        if rq.status_code != 200:
            raise Exception('Payment request {} failed: {}'.format(payment_method, rq.text))
        res = rq.json()
        if res['result'] != 'ok':
            raise Exception('Payment request {} error: {}'.format(payment_method, res['error']))
        if payment_method == 'atellixpay':
            return {'uuid': res['order_uuid']}
        elif payment_method == 'authorizenet':
            return {'uuid': res['payment_uuid']}

    def prepare_checkout(self, spec):
        cart = self.build_cart()
        cart_id = cart.sql_id()
        payments = []
        if not cart['checkout_prepared']:
            items = self.get_cart_items(cart_id, limit=1000)
            merchants = items['merchants']
            backends = {}
            for item in items['items']:
                if item['backend_id'] not in backends:
                    backends[item['backend_id']] = {
                        'total': Decimal(0),
                        'merchant': merchants[item['merchant']],
                    }
                bkdata = backends[item['backend_id']]
                item_total = Decimal(item['price']) * Decimal(item['quantity'])
                if item['net_tax'] is not None:
                    item_total = item_total + Decimal(item['net_tax'])
                bkdata['total'] = bkdata['total'] + item_total
            for bkid in backends.keys():
                backend_cart = backends[bkid]
                bkrec = sql_row('user_backend', id=bkid)
                if not bkrec.exists():
                    raise Exception('Invalid user backend: {}'.format(bkid))
                bkcfg = json.loads(bkrec['config_data'])
                backend = bkrec['backend_name']
                backend_rc = self.get_backend_record(cart_id, bkid)
                backend_data = json.loads(backend_rc['backend_data'])
                backend_payments = []
                if backend == 'vendure':
                    vb = VendureBackend(bkid, None, URIRef(backend_cart['merchant']['id']), bkcfg['vendure_url'])
                    vb.set_auth_token(backend_data['auth'])
                    vb.set_customer(spec['spec']['shippingAddress'])
                    res = vb.prepare_checkout(backend_cart['merchant'], spec['spec'])
                    log_warn(f'Vendure Prepare Checkout: {res}')
                    payment_method = spec['spec']['paymentMethod'][backend_cart['merchant']['id']]
                    payment_data = self.request_payment(bkcfg['vendure_url'], payment_method, str(backend_cart['total']), backend_data['code'])
                    backend_payments.append({
                        'method': payment_method,
                        'total': str(backend_cart['total']),
                        'data': payment_data,
                    })
                backend_data['payments'] = backend_payments
                backend_rc.update({
                    'backend_data': json.dumps(backend_data),
                })
                payments = payments + backend_payments
            cart.update({
                'checkout_prepared': True,
                'ts_updated': sql_now(),
            })
        else:
            for bkid in self.get_cart_backends(cart_id):
                bkrec = sql_row('user_backend', id=bkid)
                if not bkrec.exists():
                    raise Exception('Invalid user backend: {}'.format(bkid))
                backend = bkrec['backend_name']
                backend_rc = self.get_backend_record(cart_id, bkid)
                backend_data = json.loads(backend_rc['backend_data'])
                if backend == 'vendure':
                    bkcfg = json.loads(bkrec['config_data'])
                    user = sql_row('user', id=bkrec['user_id'])
                    merchant_uri = user['merchant_uri']
                    vb = VendureBackend(bkid, None, URIRef(merchant_uri), bkcfg['vendure_url'])
                    vb.set_auth_token(backend_data['auth'])
                    vb.set_customer(spec['spec']['shippingAddress'])
                    vb.set_billing_address(spec['spec']['billingAddress'])
                    vb.set_shipping_address(spec['spec']['shippingAddress'])
                # Update payments if necessary
                payments = payments + backend_data['payments']
        return {
            'payments': payments
        }

    def checkout_complete(self):
        cart = self.build_cart()
        cart.update({'checkout_complete': True})
        new_cart = self.build_cart(new_cart=True)
        cart_data = new_cart.data()
        cart_data['cart_data'] = {}
        cart_data['cart_items'] = self.get_cart_items(new_cart.sql_id())
        return cart_data

