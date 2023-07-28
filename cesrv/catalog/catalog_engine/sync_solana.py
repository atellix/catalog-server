import requests
from flask import current_app as app
from note.sql import * 
from note.logging import *

from .sync_data import DataSync

class SyncSolana(DataSync):
    def __init__(self, catalog_id, engine):
        self.catalog_id = catalog_id
        self.catalog_engine = engine
        self.src_data = {}
        self.dst_data = {}

    def load(self):
        # Get source data
        url = app.config['SOLANA_TRACKER'] + 'listing_collection'
        #log_warn(f'Solana Tracker: {url}')
        rq = requests.post(url, json={'catalog': self.catalog_id})
        if rq.status_code != 200:
            raise Exception('Request failed: {}'.format(rq.text))
        res = rq.json()
        if res['result'] != 'ok':
            raise Exception('Request error: {}'.format(res['error']))
        #log_warn('Listing Collection')
        #log_warn(res)
        for k in res['collection']:
            self.src_data[k] = True
        # Get destination data
        dq = nsql.table('listing_posted').get(
            select = ['listing_account'],
            where = {
                'deleted': False,
                'catalog_id': self.catalog_id,
            },
        )
        for r in dq:
            self.dst_data[r['listing_account']] = True

    def src_items(self):
        return self.src_data.keys()

    def src_has(self, item):
        res = item in self.src_data
        return res

    def dst_items(self):
        return self.dst_data.keys()

    def dst_has(self, item):
        res = item in self.dst_data
        return res

    def dst_add(self, item):
        url = app.config['SOLANA_TRACKER'] + 'listing'
        rq = requests.post(url, json={'account': item, 'defer_lookups': True})
        if rq.status_code != 200:
            raise Exception('Request failed: {}'.format(rq.text))
        res = rq.json()
        if res['result'] != 'ok':
            raise Exception('Request error: {}'.format(res['error']))
        res['account'] = item
        if self.catalog_engine.post_solana_listing(res):
            log_info(f'Added Listing: {item}')
        else:
            log_info(f'Listing Not Added: {item}')

    def dst_delete(self, item):
        if self.catalog_engine.remove_solana_listing({'listing': item}):
            log_info(f'Removed Listing: {item}')
        else: 
            log_info(f'Listing Not Removed: {item}')

