from flask import Blueprint, current_app, request
from flask_restful import Api

api_bp = Blueprint('api_bp', __name__, template_folder='templates', url_prefix='/api/catalog')
api_rest = Api(api_bp)

@api_bp.after_request
def add_header(response):
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin')
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

from app.api.rest import listing, commerce, system, uri, media, protocol

