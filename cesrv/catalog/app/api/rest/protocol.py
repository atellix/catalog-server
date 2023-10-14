import traceback
from flask import current_app as app, jsonify, request

from note.logging import *
from app.api.rest.base import BaseResource, CommandResource
from app.api import api_rest
from app.session import disable_session
from catalog_engine import CatalogEngine, sql_transaction

class ListingQuery(CommandResource, BaseResource):
    class Commands:
        @disable_session
        @sql_transaction
        def get_listings(self, **data):
            ce = CatalogEngine()
            res = ce.query_listings(data)
            return jsonify(res)

api_rest.add_resource(ListingQuery, '/query')

class CategoryQuery(CommandResource, BaseResource):
    class Commands:
        @disable_session
        @sql_transaction
        def get_category_list(self, **data):
            ce = CatalogEngine()
            res = ce.get_category_list(data)
            return jsonify(res)

        @disable_session
        @sql_transaction
        def get_category_entries(self, **data):
            ce = CatalogEngine()
            res = ce.get_category_entries(data)
            return jsonify(res)

api_rest.add_resource(CategoryQuery, '/category')

class SearchQuery(CommandResource, BaseResource):
    class Commands:
        @disable_session
        @sql_transaction
        def search(self, **data):
            ce = CatalogEngine()
            res = ce.get_entries_by_search(data)
            return jsonify(res)

api_rest.add_resource(SearchQuery, '/search')

class OrderProcessor(CommandResource, BaseResource):
    class Commands:
        @disable_session
        @sql_transaction
        def prepare_order(self, **data):
            ce = CatalogEngine()
            res = ce.prepare_order(data)
            return jsonify(res)

        @disable_session
        @sql_transaction
        def checkout(self, **data):
            ce = CatalogEngine()
            res = ce.checkout(data)
            return jsonify(res)

api_rest.add_resource(OrderProcessor, '/order')
