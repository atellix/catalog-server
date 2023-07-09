from flask import Blueprint, current_app
from flask_restful import Api

api_bp = Blueprint('api_bp', __name__, template_folder='templates', url_prefix='/api/catalog')
api_rest = Api(api_bp)

@api_bp.after_request
def add_header(response):
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    # Required for Webpack dev application to make  requests to flask api
    # from another host (localhost:8080)
    if not current_app.config['PRODUCTION']:
        response.headers['Access-Control-Allow-Origin'] = '*'
    return response

from api.rest import listing, commerce, system, uri
