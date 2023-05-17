import time
import pprint
import typesense
from flask import current_app as app, jsonify, request

from api.rest.base import BaseResource, CommandResource
from api import api_rest
from catalog_engine import CatalogData, CatalogEngine

class System(CommandResource, BaseResource):
    class Commands:
        def import_uris(self, **data):
            cd = CatalogData()
            for fk in [
                #'categories_combined',
                #'gpc_categories',
                #'pto_extracted_fixed',
                #'country_us_list',
            ]:
                fn = 'import/{}.txt'.format(fk)
                ct = 0
                with open(fn, 'r') as fp:
                    for line in fp:
                        uri = line.strip()
                        cd.store_uri_hash(uri)
                        ct = ct + 1
                        if ct % 100 == 0:
                            print(ct, fn)
                        if ct % 10000 == 0:
                            print('Sleep')
                            time.sleep(3)
            res = {}
            res['result'] = 'ok'
            return res

        def build_category_index(self, **data):
            cd = CatalogData()
            catalogs = {
                'categories_events': 'category_event',
                'categories_realestate': 'category_realestate',
            }
            for fk in [
                'categories_events',
                'categories_realestate',
                'categories_commerce',
                'gpc_categories',
                'pto_extracted_fixed',
            ]:
                fn = 'import/{}.txt'.format(fk)
                cat = 'category_commerce'
                if fk in catalogs:
                    cat = catalogs[fk]
                with open(fn, 'r') as fp:
                    ct = 0
                    for line in fp:
                        cd.index_category(line.strip(), catalog_index=cat)
                        ct = ct + 1
                        if ct % 100 == 0:
                            print(ct, fn)
                        if ct % 5000 == 0:
                            print('Sleep')
                            time.sleep(3)
                        #if ct > 20:
                        #    break
            res = {}
            res['result'] = 'ok'
            return res

        def build_location_index(self, **data):
            cd = CatalogData()
            for fk in [
                'country_us_list',
            ]:
                fn = 'import/{}.txt'.format(fk)
                with open(fn, 'r') as fp:
                    ct = 0
                    for line in fp:
                        cd.index_location(line.strip())
                        ct = ct + 1
                        if ct % 100 == 0:
                            print(ct, fn)
                        if ct % 5000 == 0:
                            print('Sleep')
                            time.sleep(3)
                        #if ct > 5:
                        #    break
            res = {}
            res['result'] = 'ok'
            return res

        def sync_catalog(self, **data):
            cs = CatalogEngine()
            res = cs.sync_solana_catalog(catalog=data['catalog'])
            return res

        def post_listing(self, **data):
            print('Post Listing', data)
            res = {}
            cs = CatalogEngine()
            cs.post_solana_listing(data['listing'])
            res['result'] = 'ok'
            return res

        def remove_listing(self, **data):
            print('Remove Listing', data)
            res = {}
            cs = CatalogEngine()
            cs.remove_solana_listing(data)
            res['result'] = 'ok'
            return res

api_rest.add_resource(System, '/system')

