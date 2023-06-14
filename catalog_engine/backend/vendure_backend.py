import json
import pprint

from .vendure.vendure_client import VendureClient
from .vendure.vendure_record import VendureRecordBuilder
from .vendure.vendure_sync import VendureSync
from .vendure.vendure_cart import VendureCart

class VendureBackend(object):
    def __init__(self, graph, merchant_uri, shop_api):
        self.graph = graph
        self.shop_api = shop_api
        self.merchant_uri = merchant_uri
        self.vendure_client = VendureClient(self.shop_api)

    def set_auth_token(self, auth_token):
        self.vendure_client.set_auth_token(auth_token)

    def build_product(self, product_id):
        vcl = self.vendure_client
        vrb = VendureRecordBuilder(vcl, self.graph)
        detail = vcl.get_product(product_id)
        return vrb.build_product(detail, self.merchant_uri, link_collections=False)

    def build_product_list(self, collection_slug):
        vcl = self.vendure_client
        vrb = VendureRecordBuilder(vcl, self.graph)
        ctd = vrb.get_catalog_category(collection_slug)
        return vrb.build_product_list(ctd, collection_slug, self.merchant_uri)

    def get_collection(self, collection_slug):
        vcl = self.vendure_client
        vrb = VendureRecordBuilder(vcl, self.graph)
        return vrb.get_catalog_category(collection_slug)

    def build_catalog(self):
        vcl = self.vendure_client
        vrb = VendureRecordBuilder(vcl, self.graph)
        return vrb.build_catalog()

    def sync_merchant(self, root_id):
        vcl = self.vendure_client
        vrb = VendureRecordBuilder(vcl, self.graph)
        cat_list = vrb.get_catalog_categories(self.merchant_uri, root_id=root_id)
        snc = VendureSync(vcl)
        return snc.sync_merchant(cat_list)

    def summarize_product_spec(self, obj):
        vrb = VendureRecordBuilder(self.vendure_client, self.graph)
        return vrb.summarize_product_spec(obj)

    def get_product_spec(self, product_id):
        vcl = VendureClient(self.shop_api)
        vrb = VendureRecordBuilder(vcl, self.graph)
        detail = vcl.get_product(product_id)
        return vrb.build_product_spec(detail, self.merchant_uri)

    def get_product_item_spec(self, detail):
        vcl = VendureClient(self.shop_api)
        vrb = VendureRecordBuilder(vcl, self.graph)
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

    def prepare_checkout(self, merchant, spec):
        vcl = self.vendure_client
        cart = VendureCart(vcl)
        return cart.prepare_checkout(merchant, spec)

