""" API Backend - Base Resource Models """

from flask import request, jsonify, session
from flask_restful import Resource, abort
#from api.security import require_auth

from note.logging import log_error

class BaseResource(Resource):
    def get(self, *args, **kwargs):
        abort(405)

    def post(self, *args, **kwargs):
        abort(405)

    def put(self, *args, **kwargs):
        abort(405)

    def patch(self, *args, **kwargs):
        abort(405)

    def delete(self, *args, **kwargs):
        abort(405)

#class SecureResource(BaseResource):
#    method_decorators = [require_auth]

class CommandResource(object):
    """ Receive commands from the client """
    def post(self, *args, **kwargs):
        req = request.json
        if not isinstance(req, dict):
            abort(500)
        cmd = req['command']
        del req['command']
        if cmd.startswith('_'):
            raise Exception('Invalid command specification: {}'.format(cmd))
        inst = self.Commands()
        method = getattr(self.Commands, cmd, None)
        if method is None:
            abort(404)
        if isinstance(res, dict):
            return jsonify(res)
        else:
            return res

