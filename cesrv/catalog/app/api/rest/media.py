from flask import current_app as app, Response, abort, jsonify, make_response

from app.api import api_rest
from app.api.rest.base import BaseResource
from app.session import disable_session
from note.logging import *
from catalog_engine import sql_transaction
from util.media_cache import MediaCache

class Media(BaseResource):
    @disable_session
    @sql_transaction
    def get(self, *args, **kwargs):
        mc = MediaCache(None)
        pc = kwargs.get('base58_public_key', '')
        data, mime_type = mc.get_data_by_key(pc)
        if data is None:
            abort(404)
        response = make_response(data)
        if mime_type is not None and len(mime_type) > 0:
            response.headers.set('Content-Type', mime_type)
        return response

api_rest.add_resource(Media, '/media/<base58_public_key>/<filename>')

