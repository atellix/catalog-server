import json

from .. import CatalogBackend
from .vendure.vendure_client import VendureClient
from .vendure.vendure_record import VendureRecordBuilder

class VendureBackend(CatalogBackend):
    def __init__(self, graph, merchant_uri, shop_api):
        self.graph = graph
        self.merchant_uri = merchant_uri
        self.shop_api = shop_api

    def build_product(self, product_id):
        vcl = VendureClient(self.shop_api)
        vrb = VendureRecordBuilder(vcl, self.graph)
        detail = vcl.get_product(product_id)
        return vrb.build_product(detail, self.merchant_uri, link_collections=False)

    def build_product_list(self, collection_slug):
        vcl = VendureClient(self.shop_api)
        vrb = VendureRecordBuilder(vcl, self.graph)
        ctd = vrb.get_catalog_category(collection_slug)
        return vrb.build_product_list(ctd, self.merchant_uri)

    def build_catalog(self):
        vcl = VendureClient(self.shop_api)
        vrb = VendureRecordBuilder(vcl, self.graph)
        return vrb.build_catalog()

