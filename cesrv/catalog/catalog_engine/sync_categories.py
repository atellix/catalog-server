import json
from note.sql import * 
from note.logging import *
from .sync_data import DataSync

class SyncCategories(DataSync):
    def __init__(self, user_id, entry_id, spec):
        self.user_id = user_id
        self.entry_id = entry_id
        self.spec = spec
        self.src_data = {}
        self.dst_data = {}
        self.update = True

    def load(self):
        etq = nsql.table('entry_listing').get(
            select = ['distinct u.uri'],
            table = ['entry_listing el', 'listing_posted lp, uri u'],
            join = ['el.listing_posted_id=lp.id', 'lp.category_hash=u.uri_hash'],
            where = {'el.entry_id': self.entry_id},
            result = list,
        )
        src_data = {}
        for irc in etq:
            internal_uri = irc[0]
            pub_cats = nsql.table('category_internal').get(
                select = ['distinct cpi.public_id'],
                table = 'category_internal ci, category_public_internal cpi',
                join = ['ci.id=cpi.internal_id'],
                where = {'ci.internal_uri': internal_uri},
                result = list,
            )
            for pc in pub_cats:
                src_data[str(pc[0])] = True
        self.src_data = src_data
        ctq = nsql.table('entry_category').get(
            select = ['public_id'],
            where = {'entry_id': self.entry_id},
        )
        for r in ctq:
            self.dst_data[str(r['public_id'])] = True

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
        sql_insert('entry_category', {
            'user_id': self.user_id,
            'entry_id': self.entry_id,
            'public_id': item,
            'name': self.spec.get('name', None),
            'price': self.spec.get('price', None),
            'brand': self.spec.get('brand', None),
        })

    def dst_delete(self, item):
        rc = sql_row('entry_category', entry_id=self.entry_id, public_id=item)
        if rc.exists():
            rc.delete()

    def dst_eq(self, item):
        orig_item = sql_row('entry_category', entry_id=self.entry_id, public_id=item)
        new_item = sql_row('entry', id=self.entry_id)
        new_data = json.loads(new_item['data_index'])
        if (
            orig_item['name'] == new_data.get('name', None) and
            orig_item['price'] == new_data.get('price', None) and
            orig_item['brand'] == new_data.get('brnad', None)
        ):
            return False, None, None
        return True, orig_item, new_data

    def dst_update(self, item, orig_item, new_data):
        orig_item.update({
            'name': new_data.get('name', None),
            'price': new_data.get('price', None),
            'brand': new_data.get('brand', None),
        })

