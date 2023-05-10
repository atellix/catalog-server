from flask import current_app as app, jsonify, request

from api.rest.base import BaseResource, CommandResource
from api import api_rest
from catalog_engine import CatalogData

class System(CommandResource, BaseResource):
    class Commands:
        def import_uris(self, **data):
            cd = CatalogData()
            for fk in [
                #'country_us_list',
                #'gpc_categories',
                #'alpha_categories',
                #'pto_extracted',
            ]:
                fn = 'import/{}.txt'.format(fk)
                with open(fn, 'r') as fp:
                    for line in fp:
                        uri = line.strip()
                        cd.store_uri_hash(uri)
            res = {}
            res['result'] = 'ok'
            return res

api_rest.add_resource(System, '/system')

