from flask import current_app as app, Response, abort, jsonify

from app.api import api_rest
from app.api.rest.base import BaseResource
from app.session import disable_session
from catalog_engine import CatalogData

class URI(BaseResource):
    @disable_session
    def get(self, *args, **kwargs):
        cd = CatalogData()
        res = None
        try:
            res = cd.get_encoded_uri(kwargs.get('base58_hashed_uri', ''))
        except Exception as e:
            pass
        if res is None:
            abort(404)
        return Response(res, mimetype='text/plain')

api_rest.add_resource(URI, '/uri/<base58_hashed_uri>')

class URIGraph(BaseResource):
    @disable_session
    def get(self, *args, **kwargs):
        cd = CatalogData()
        res = {}
        try:
            ruri = cd.get_encoded_uri(kwargs.get('base58_hashed_uri', ''))
            if ruri is None:
                abort(404)
            res['uri'] = ruri
            res['graph'] = cd.get_resource(ruri)
        except Exception as e:
            abort(500)
        res['result'] = 'ok'
        return jsonify(res)

api_rest.add_resource(URIGraph, '/graph/<base58_hashed_uri>')

