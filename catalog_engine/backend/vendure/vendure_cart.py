import uuid
import json
import pprint 
from decimal import Decimal
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

    def prepare_checkout(self, merchant, spec):
        vcl = self.vendure_client
        rc = vcl.set_customer(
            title='',
            firstName='Some',
            lastName='Body',
            emailAddress='',
            phoneNumber='',
        )
        ship_methods = vcl.get_shipping()
        rc = vcl.set_shipping_method(ship_methods['eligibleShippingMethods'][0]['id'])
        rc = vcl.set_shipping_address(**{
            'fullName': 'Some Body',
            'company': 'Some Co',
            'streetLine1': '123 Front',
            'streetLine2': 'NA',
            'city': 'Columbus',
            'province': 'OH',
            'postalCode': '43210',
            'countryCode': 'US',
            'phoneNumber': '+13103512344',
        })
        rc = vcl.set_billing_address(**{
            'fullName': 'Some Body',
            'company': 'Some Co',
            'streetLine1': '123 Front',
            'streetLine2': 'NA',
            'city': 'Columbus',
            'province': 'OH',
            'postalCode': '43210',
            'countryCode': 'US',
            'phoneNumber': '+13103512344',
        })
        rc = vcl.set_state('ArrangingPayment')
        rc = vcl.set_payment_method('atellixpay')
        return rc

