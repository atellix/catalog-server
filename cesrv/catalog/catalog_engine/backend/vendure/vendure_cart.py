import uuid
import json
import pprint 
from decimal import Decimal

from note.logging import *
#import based58
#import canonicaljson
#from rdflib import Graph, Literal, URIRef, Namespace, BNode
#from rdflib.namespace import RDF, SKOS, RDFS, XSD, OWL, DC, DCTERMS

class VendureCart(object):
    def __init__(self, vendure_client):
        self.vendure_client = vendure_client

    def get_cart(self):
        pass

    def add_to_cart(self, product_variant_id, quantity):
        vcl = self.vendure_client
        res = vcl.add_to_cart(product_variant_id, quantity)
        line = None
        price_with_tax = None
        if 'lines' not in res['addItemToOrder']:
            raise Exception('Invalid add_to_cart result from Vendure: {}'.format(pprint.pformat(res)))
        for l in res['addItemToOrder']['lines']:
            if str(l['productVariant']['id']) == str(product_variant_id):
                line = l['id']
                price_with_tax = Decimal(l['linePriceWithTax']) / Decimal(100)
                break
        if not line:
            raise Exception('No line ID for product variant: {}'.format(product_variant_id))
        return {
            'auth': vcl.auth_token,
            'line': line,
            'code': res['addItemToOrder']['code'],
            'net_price': str(price_with_tax),
        }

    def update_cart(self, line_id, quantity):
        vcl = self.vendure_client
        res = vcl.update_cart(line_id, quantity)
        line = None
        price_with_tax = None
        for l in res['adjustOrderLine']['lines']:
            if str(l['id']) == str(line_id):
                price_with_tax = Decimal(l['linePriceWithTax']) / Decimal(100)
                break
        return {
            'auth': vcl.auth_token,
            #'code': res['adjustOrderLine']['code'],
            'net_price': str(price_with_tax),
        }

    def remove_from_cart(self, line_id):
        vcl = self.vendure_client
        res = vcl.remove_from_cart(line_id)
        return {
            'auth': vcl.auth_token,
            #'code': res['removeOrderLine']['code'],
        }

    def get_shipping_methods(self):
        vcl = self.vendure_client
        ship_methods = vcl.get_shipping()
        return ship_methods['eligibleShippingMethods']

    def set_customer(self, spec):
        vcl = self.vendure_client
        rc = vcl.set_customer(
            title = '',
            firstName = spec.get('firstName', ''),
            lastName = spec.get('lastName', ''),
            emailAddress = spec.get('email', ''),
            phoneNumber = spec.get('phone', ''),
        )
        #print(f'Set Customer: {rc}')
        return {
            'auth': vcl.auth_token,
        }

    def set_shipping_address(self, spec):
        vcl = self.vendure_client
        rc = vcl.set_shipping_address(**{
            'fullName': '{} {}'.format(spec.get('firstName', ''), spec.get('lastName', '')),
            'company': spec.get('company', ''),
            'streetLine1': spec.get('address', ''),
            'streetLine2': spec.get('address2', ''),
            'city': spec.get('city', ''),
            'province': spec.get('region', ''),
            'postalCode': spec.get('postcode', ''),
            'countryCode': spec.get('country', ''),
            'phoneNumber': spec.get('phone', ''),
        })
        #print(f'Set Shipping Address: {rc}')
        return {
            'auth': vcl.auth_token,
        }

    def set_billing_address(self, spec):
        vcl = self.vendure_client
        rc = vcl.set_billing_address(**{
            'fullName': '{} {}'.format(spec.get('firstName', ''), spec.get('lastName', '')),
            'company': spec.get('company', ''),
            'streetLine1': spec.get('address', ''),
            'streetLine2': spec.get('address2', ''),
            'city': spec.get('city', ''),
            'province': spec.get('region', ''),
            'postalCode': spec.get('postcode', ''),
            'countryCode': spec.get('country', 'us'),
            'phoneNumber': spec.get('phone', ''),
        })
        #print(f'Set Shipping Address: {rc}')
        return {
            'auth': vcl.auth_token,
        }

    def set_shipping_method(self, method_id):
        vcl = self.vendure_client
        rc = vcl.set_shipping_method(method_id)
        ship_data = rc['setOrderShippingMethod']
        ship_price = Decimal(ship_data['shipping']) / Decimal(100)
        ship_net = Decimal(ship_data['shippingWithTax']) / Decimal(100)
        if ship_net < ship_price:
            raise Exception('Shipping with tax less than shipping cost')
        ship_tax = ship_net - ship_price
        #print(f'Shipping Price: {ship_price} Shipping Tax: {ship_tax}')
        return {
            'auth': vcl.auth_token,
            'price': ship_price,
            'tax': ship_tax,
        }
 
    def prepare_checkout(self, merchant, spec):
        log_warn('Vendure Prepare Checkout')
        vcl = self.vendure_client
        billing = spec['billingAddress']
        rc = vcl.set_billing_address(**{
            'fullName': '{} {}'.format(billing.get('firstName', ''), billing.get('lastName', '')),
            'company': billing.get('company', ''),
            'streetLine1': billing.get('address', ''),
            'streetLine2': billing.get('address2', ''),
            'city': billing.get('city', ''),
            'province': billing.get('region', ''),
            'postalCode': billing.get('postcode', ''),
            'countryCode': billing.get('country', 'us'),
            'phoneNumber': billing.get('phone', ''),
        })
        shipping = spec['shippingAddress']
        rc = vcl.set_shipping_address(**{
            'fullName': '{} {}'.format(shipping.get('firstName', ''), shipping.get('lastName', '')),
            'company': shipping.get('company', ''),
            'streetLine1': shipping.get('address', ''),
            'streetLine2': shipping.get('address2', ''),
            'city': shipping.get('city', ''),
            'province': shipping.get('region', ''),
            'postalCode': shipping.get('postcode', ''),
            'countryCode': shipping.get('country', ''),
            'phoneNumber': shipping.get('phone', ''),
        })
        rc = vcl.set_state('ArrangingPayment')
