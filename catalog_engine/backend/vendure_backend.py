from .. import CatalogBackend
from .vendure.vendure_client import VendureClient
from .vendure.vendure_record import VendureRecordBuilder

class VendureBackend(CatalogBackend):
    def __init__(self, merchant_uri, shop_api):
        self.merchant_uri = merchant_uri
        self.shop_api = shop_api

    def build_product(self, graph, product_id):
        vcl = VendureClient(self.shop_api)
        vrb = VendureRecordBuilder(vcl, graph)
        return vrb.build_product(product_id, self.merchant_uri, link_collections=False)

    def build_catalog(self, graph):
        vcl = VendureClient(self.shop_api)
        vrb = VendureRecordBuilder(vcl, graph)
        return vrb.build_catalog()

