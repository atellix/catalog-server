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

