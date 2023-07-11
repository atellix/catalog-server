from flask import current_app as app, jsonify, request

from app.api.rest.base import BaseResource, CommandResource
from app.api import api_rest
from app.session import disable_session
from catalog_engine import CatalogEngine

class Listing(CommandResource, BaseResource):
    class Commands:
        @disable_session
        def sign_listing(self, **data):
            res = {}
            ce = CatalogEngine()
            sign_cfg = {
                'catalog_program': app.config['CATALOG_PROGRAM'],
                'signer_secret': app.config['CATALOG_SIGNER'],
                'fee_mint': app.config['CATALOG_FEE_MINT'],
                'fee_account': app.config['CATALOG_FEE_ACCOUNT'],
                'fee_tokens': 0,
            }
            res.update(ce.sign_listing(sign_cfg, data))
            res['result'] = 'ok'
            return res

        @disable_session
        def set_listing(self, **data):
            ce = CatalogEngine()
            return ce.set_listing(data)

        @disable_session
        def get_listing(self, **data):
            ce = CatalogEngine()
            return ce.get_listing(data)

        @disable_session
        def set_record(self, **data):
            ce = CatalogEngine()
            return ce.set_record(data)

        @disable_session
        def get_record(self, **data):
            ce = CatalogEngine()
            return ce.get_record(data)

api_rest.add_resource(Listing, '/listing')

class ListingEntry(BaseResource):
    @disable_session
    def get(self, *args, **kwargs):
        ce = CatalogEngine()
        res = ce.get_listing({'listing': request.view_args['listing_uuid']})
        return jsonify(res)

api_rest.add_resource(ListingEntry, '/listing/<listing_uuid>')


