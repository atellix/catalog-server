import json
import pprint

from .vendure.vendure_client import VendureClient
from .vendure.vendure_record import VendureRecordBuilder
from .vendure.vendure_sync import VendureSync
from .vendure.vendure_cart import VendureCart

class VendureBackend(object):
    def __init__(self, backend_id, graph, merchant_uri, shop_api):
        self.backend_id = backend_id
        self.graph = graph
        self.shop_api = shop_api
        self.merchant_uri = merchant_uri
        self.vendure_client = VendureClient(self.shop_api)
        if merchant_uri.endswith('/'):
            merchant_uri = merchant_uri[:-1]
        self.base_uri = '{}/vendure.{}/'.format(merchant_uri, backend_id)

    def set_auth_token(self, auth_token):
        self.vendure_client.set_auth_token(auth_token)

    def get_collection(self, collection_slug):
        vcl = self.vendure_client
        vrb = VendureRecordBuilder(vcl, self.graph, self.base_uri)
        return vrb.get_catalog_category(collection_slug)

    def sync_listings(self, user, catalog_id, backend_id, root_id):
        vcl = self.vendure_client
        vrb = VendureRecordBuilder(vcl, self.graph, self.base_uri)
        cat_list = vrb.get_catalog_categories(self.merchant_uri, root_id=root_id)
        snc = VendureSync(vcl)
        return snc.sync_listings(user, catalog_id, backend_id, cat_list)

    def summarize_product_spec(self, obj):
        vrb = VendureRecordBuilder(self.vendure_client, self.graph, self.base_uri)
        return vrb.summarize_product_spec(obj)

    def get_product_spec(self, product_id, user_id):
        vcl = VendureClient(self.shop_api)
        vrb = VendureRecordBuilder(vcl, self.graph, self.base_uri)
        detail = vcl.get_product(product_id)
        return vrb.build_product_spec(detail, self.merchant_uri, user_id)

    def get_product_item_spec(self, detail):
        vcl = VendureClient(self.shop_api)
        vrb = VendureRecordBuilder(vcl, self.graph, self.base_uri)
        return vrb.build_product_item_spec(detail)

    def get_cart(self):
        pass

    def add_to_cart(self, product_variant_id, quantity):
        vcl = self.vendure_client
        cart = VendureCart(vcl)
        return cart.add_to_cart(product_variant_id, quantity)

    def update_cart(self, line_id, quantity):
        vcl = self.vendure_client
        cart = VendureCart(vcl)
        return cart.update_cart(line_id, quantity)

    def remove_from_cart(self, line_id):
        vcl = self.vendure_client
        cart = VendureCart(vcl)
        return cart.remove_from_cart(line_id)

    def set_customer(self, spec):
        vcl = self.vendure_client
        cart = VendureCart(vcl)
        return cart.set_customer(spec)

    def get_shipping(self):
        vcl = self.vendure_client
        cart = VendureCart(vcl)
        return cart.get_shipping_methods()

    def set_shipping(self, method_id, spec):
        vcl = self.vendure_client
        cart = VendureCart(vcl)
        return cart.set_shipping_method(method_id)

    def set_shipping_address(self, spec):
        vcl = self.vendure_client
        cart = VendureCart(vcl)
        return cart.set_shipping_address(spec)

    def set_billing_address(self, spec):
        vcl = self.vendure_client
        cart = VendureCart(vcl)
        return cart.set_billing_address(spec)

    def prepare_checkout(self, merchant, spec):
        vcl = self.vendure_client
        cart = VendureCart(vcl)
        return cart.prepare_checkout(merchant, spec)

