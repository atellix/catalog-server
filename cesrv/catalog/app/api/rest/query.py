import traceback
from flask import current_app as app, jsonify, request

from note.logging import *
from app.api.rest.base import BaseResource, CommandResource
from app.api import api_rest
from app.session import disable_session
from catalog_engine import CatalogEngine, authorize_user

class ListingQuery(CommandResource, BaseResource):
    class Commands:
        @disable_session
        def get_listings(self, **data):
            ce = CatalogEngine()
            res = ce.query_listings(data)
            return jsonify(res)

api_rest.add_resource(ListingQuery, '/query')
