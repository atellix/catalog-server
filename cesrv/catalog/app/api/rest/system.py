import time
import pprint
import requests
import typesense
from flask import current_app as app, jsonify, request

from note.logging import *

from app.api.rest.base import BaseResource, CommandResource
from app.api import api_rest
from app.session import disable_session
from catalog_engine import CatalogData, CatalogEngine, authorize_admin, sql_transaction

ADMIN_JWT_CLAIMS = {'iss': 'atellix-network', 'aud': 'atellix-catalog', 'sub': 'catalog-admin'}
SOLANA_JWT_CLAIMS = {'iss': 'atellix-network', 'aud': 'atellix-catalog', 'sub': 'catalog-data-1'}

class System(CommandResource, BaseResource):
    class Commands:
        @disable_session
        @authorize_admin('admin', ADMIN_JWT_CLAIMS)
        def create_user(self, **data):
            res = {}
            cs = CatalogEngine()
            res.update(cs.create_user(data))
            return res

        @disable_session
        @authorize_admin('admin', ADMIN_JWT_CLAIMS)
        def update_user(self, **data):
            res = {}
            cs = CatalogEngine()
            res.update(cs.update_user(data))
            return res

        @disable_session
        @authorize_admin('admin', ADMIN_JWT_CLAIMS)
        def import_uris(self, **data):
            cd = CatalogData()
            for fk in [
                #'categories_commerce',
                #'categories_events',
                #'categories_realestate',
                #'country_us_list',
                #'gpc_categories',
                #'pto_extracted_fixed',
                'google_product_taxonomy_uris',
            ]:
                fn = 'import/{}.txt'.format(fk)
                ct = 0
                with open(fn, 'r') as fp:
                    log_warn('Begin import: {}'.format(fn))
                    for line in fp:
                        uri = line.strip()
                        cd.store_uri_hash(uri)
                        ct = ct + 1
                        if ct % 100 == 0:
                            log_warn('{} {}'.format(ct, fn))
                        if ct % 10000 == 0:
                            log_warn('Sleep')
                            time.sleep(3)
            res = {}
            res['result'] = 'ok'
            return res

        @disable_session
        @authorize_admin('admin', ADMIN_JWT_CLAIMS)
        def build_category_index(self, **data):
            cd = CatalogData()
            #cd.create_category_index(delete=data.get('delete', False))
            catalogs = {
                'categories_events': 'category_event',
                'categories_realestate': 'category_realestate',
            }
            for fk in [
                #'categories_events',
                #'categories_realestate',
                #'categories_commerce',
                #'gpc_categories',
                #'pto_extracted_fixed',
                'google_product_taxonomy_uris',
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
                            log_warn('{} {}'.format(ct, fn))
                        if ct % 5000 == 0:
                            log_warn('Sleep')
                            time.sleep(3)
                        #if ct > 20:
                        #    break
            res = {}
            res['result'] = 'ok'
            return res

        @disable_session
        @authorize_admin('admin', ADMIN_JWT_CLAIMS)
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
                            log_warn('{} {}'.format(ct, fn))
                        if ct % 5000 == 0:
                            log_warn('Sleep')
                            time.sleep(3)
                        #if ct > 5:
                        #    break
            res = {}
            res['result'] = 'ok'
            return res

        @disable_session
        @authorize_admin('admin', ADMIN_JWT_CLAIMS)
        def sync_catalog(self, **data):
            cs = CatalogEngine()
            res = cs.sync_solana_catalog(catalog=data['catalog'])
            return res

        @disable_session
        @authorize_admin('admin', ADMIN_JWT_CLAIMS)
        def sync_listing(self, **data):
            url = app.config['SOLANA_TRACKER'] + 'sync_listing'
            rq = requests.post(url, json={'pubkey': data['pubkey']})
            if rq.status_code != 200:
                raise Exception('Request failed: {}'.format(rq.text))
            return rq.json()

        @disable_session
        @authorize_admin('admin', ADMIN_JWT_CLAIMS)
        def create_catalog_index(self, **data):
            cd = CatalogData()
            cd.create_catalog_index(delete=data.get('delete', False))
            res = {}
            res['result'] = 'ok'
            return res

        @disable_session
        @authorize_admin('admin', ADMIN_JWT_CLAIMS)
        def build_catalog(self, **data):
            cs = CatalogEngine()
            cs.build_catalog(catalog=data['catalog'], reindex=data.get('reindex', False))
            res = {}
            res['result'] = 'ok'
            return res

### Solana tracker

        @disable_session
        @sql_transaction
        #@authorize_admin('solana', SOLANA_JWT_CLAIMS)
        def post_listing(self, **data):
            #print('Post Listing', data)
            res = {}
            cs = CatalogEngine()
            cs.post_solana_listing(data['listing'])
            res['result'] = 'ok'
            return res

        @disable_session
        @sql_transaction
        #@authorize_admin('solana', SOLANA_JWT_CLAIMS)
        def remove_listing(self, **data):
            #print('Remove Listing', data)
            res = {}
            cs = CatalogEngine()
            cs.remove_solana_listing(data)
            res['result'] = 'ok'
            return res

api_rest.add_resource(System, '/system')

