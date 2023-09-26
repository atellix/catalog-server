import traceback
from flask import current_app as app, jsonify, request

from note.logging import *
from app.api.rest.base import BaseResource, CommandResource
from app.api import api_rest
from app.session import disable_session
from catalog_engine import CatalogEngine, authorize_user

class Listing(CommandResource, BaseResource):
    class Commands:
        @disable_session
        @authorize_user
        def sign_listing(self, **data):
            res = {}
            ce = CatalogEngine()
            try:
                sign_cfg = {
                    'catalog_program': app.config['CATALOG_PROGRAM'],
                    'signer_secret': app.config['CATALOG_SIGNER'],
                    'fee_mint': app.config['CATALOG_FEE_MINT'],
                    'fee_account': app.config['CATALOG_FEE_ACCOUNT'],
                    'fee_tokens': 0,
                }
                res.update(ce.sign_listing(sign_cfg, data))
                res['result'] = 'ok'
            except Exception as e:
                etxt = "{}: {}\n{}".format(type(e).__name__, e, ''.join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)[0:-1]))
                log_error(etxt)
                res['error'] = str(e)
                res['result'] = 'error'
            return res

        @disable_session
        @authorize_user
        def sync_listings(self, **data):
            ce = CatalogEngine()
            return ce.sync_listings(data)

        @disable_session
        @authorize_user
        def build_catalog(self, **data):
            ce = CatalogEngine()
            ce.build_catalog(catalog=data['catalog'], reindex=data.get('reindex', False), user_id=g.user.sql_id())
            res = {}
            res['result'] = 'ok'
            return res

api_rest.add_resource(Listing, '/listing')

class ListingEntry(CommandResource, BaseResource):
    def get(self, *args, **kwargs):
        ce = CatalogEngine()
        res = ce.get_listing({'listing': request.view_args['listing_uuid']})
        return jsonify(res)

    class Commands:
        @disable_session
        def get_listing_entries(self, **data):
            ce = CatalogEngine()
            res = ce.get_listing_entries(request.view_args['listing_uuid'], data)
            return jsonify(res)

api_rest.add_resource(ListingEntry, '/listing/<listing_uuid>')
