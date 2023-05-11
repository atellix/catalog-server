from flask import current_app as app, Response, abort

from api import api_rest
from api.rest.base import BaseResource
from catalog_engine import CatalogData

class URI(BaseResource):
    def get(self, *args, **kwargs):
        cd = CatalogData()
        res = None
        try:
            res = cd.get_encoded_uri(kwargs.get('base58_encoded_uri', ''))
        except Exception as e:
            pass
        if res is None:
            abort(404)
        return Response(res, mimetype='text/plain')

api_rest.add_resource(URI, '/uri/<base58_encoded_uri>')

