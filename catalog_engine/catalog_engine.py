import json
import uuid
import borsh
import pprint
import base64
import based58
import krock32
import requests
import typesense
from flask import abort, current_app as app
from borsh import types
from datetime import datetime, timedelta
from Crypto.Hash import SHAKE128
from solders.pubkey import Pubkey
from solders.keypair import Keypair

from note.sql import *

# TODO: config file or database this
CATALOGS = {
    'commerce': 0,
    'event': 1,
    'realestate': 2,
    'employment': 3,
    'investment': 4,
}

LISTING_SCHEMA = borsh.schema({
    'uuid': types.u128,
    'catalog': types.u64,
    'category': types.u128,
    'filter_by_1': types.u128,
    'filter_by_2': types.u128,
    'filter_by_3': types.u128,
    'attributes': types.u8,
    'latitude': types.fixed_array(types.u8, 4),
    'longitude': types.fixed_array(types.u8, 4),
    'owner': types.fixed_array(types.u8, 32),
    'listing_url': types.fixed_array(types.u8, 32),
    'label_url': types.fixed_array(types.u8, 32),
    'detail_url': types.fixed_array(types.u8, 32),
    'fee_account': types.fixed_array(types.u8, 32),
    'fee_tokens': types.u64,
})

class CatalogEngine():
    def __init__(self):
        pass

    def to_byte_array(self, b64_string):
        byte_string = base64.b64decode(b64_string)
        return [int(b) for b in byte_string]

    def to_text_account(self, cfg, text_string, fill_mode=0):
        shake = SHAKE128.new()
        shake.update(text_string.encode('utf8'))
        shake_hash = shake.read(16)
        seeds = [bytes([fill_mode]), shake_hash]
        pda = Pubkey.find_program_address(seeds, Pubkey.from_string(cfg['catalog_program']))
        #print(text_string)
        #print(str(pda[0]))
        return [int(b) for b in bytes(pda[0])]

# cfg:
#  - catalog_program: pubkey string
#  - signer_secret: keypair string
#  - fee_account: pubkey string
#  - fee_mint: pubkey string
#  - fee_tokens: int
    def sign_listing(self, cfg, inp):
        # Find category in database
        cat_hash = int(inp['category']).to_bytes(16, 'big')
        cat = nsql.table('uri').get(
            select = ['uri'],
            where = {'uri_hash': cat_hash},
        )
        if not(len(cat)):
            raise Exception('Invalid category uri')
        # TODO: Verify category in graph db
        # Find or create uuid
        owner_pk = based58.b58encode(base64.b64decode(inp['owner'])).decode('utf8')
        cur = sql_row('listing_lock',
            catalog_id=CATALOGS[inp['catalog']],
            category_hash=cat_hash,
            owner=owner_pk,
        )
        create_lock = True
        if cur.exists():
            tsdiff = datetime.now() - cur['ts_created']
            if tsdiff > timedelta(minutes=5):
                cur.delete()
            else:
                create_lock = False
                listing_uuid = uuid.UUID(bytes=cur['uuid'])
        if create_lock:
            listing_uuid = uuid.uuid4()
            sql_insert('listing_lock', {
                'catalog_id': CATALOGS[inp['catalog']],
                'category_hash': cat_hash,
                'owner': owner_pk,
                'uuid': listing_uuid.bytes,
                'ts_created': sql_now(),
            })
        listing_data = {
            'uuid': listing_uuid.int,
            'catalog': CATALOGS[inp['catalog']],
            'category': int(inp['category']),
            'filter_by_1': int(inp['filter_by_1']),
            'filter_by_2': int(inp['filter_by_2']),
            'filter_by_3': int(inp['filter_by_3']),
            'attributes': inp['attributes'],
            'latitude': self.to_byte_array(inp['latitude']),
            'longitude': self.to_byte_array(inp['longitude']),
            'owner': self.to_byte_array(inp['owner']),
            'listing_url': self.to_text_account(cfg, inp['listing_url']['text'], inp['listing_url']['expand']),
            'label_url': self.to_text_account(cfg, inp['label_url']['text'], inp['label_url']['expand']),
            'detail_url': self.to_text_account(cfg, inp['detail_url']['text'], inp['detail_url']['expand']),
            'fee_account': [int(b) for b in bytes(Pubkey.from_string(cfg['fee_account']))],
            'fee_tokens': cfg['fee_tokens'],
        }
        serialized_bytes = borsh.serialize(LISTING_SCHEMA, listing_data)
        decoder = krock32.Decoder(strict=False, checksum=False)
        decoder.update(cfg['signer_secret'])
        kp = Keypair.from_bytes(decoder.finalize())
        res = {}
        res['sig'] = str(kp.sign_message(serialized_bytes))
        res['uuid'] = str(listing_uuid)
        res['pubkey'] = str(kp.pubkey())
        res['catalog'] = str(CATALOGS[inp['catalog']])
        res['message'] = base64.b64encode(serialized_bytes).decode('utf8')
        res['fee_mint'] = cfg['fee_mint']
        res['fee_account'] = cfg['fee_account']
        return res

    def set_listing(self, inp):
        res = {}
        listing_uuid_bytes = uuid.UUID(inp['listing']).bytes
        user_uuid_bytes = uuid.UUID(inp['user']).bytes
        record_uuid_bytes = uuid.UUID(inp['record']).bytes
        u = sql_row('user', uuid=user_uuid_bytes)
        now = sql_now()
        if not(u.exists()):
            u = sql_insert('user', {
                'uuid': user_uuid_bytes,
                'ts_created': now,
                'ts_updated': now,
            })
        rec = sql_row('record', uuid=record_uuid_bytes)
        if not(rec.exists()):
            if inp.get('data', False):
                rec = sql_insert('record', {
                    'user_id': u.sql_id(),
                    'uuid': record_uuid_bytes,
                    'data': json.dumps(inp['data']),
                    'ts_created': now,
                    'ts_updated': now,
                })
            else:
                abort(404)
        elif inp.get('data', False):
            rec.update({
                'data': json.dumps(inp['data']),
                'ts_updated': now,
            })
        r = sql_row('listing', uuid=listing_uuid_bytes)
        if r.exists():
            if inp.get('remove', False):
                r.delete()
            else:
                r.update({
                    'record_id': rec.sql_id(),
                    'ts_updated': now,
                })
        else:
            sql_insert('listing', {
                'uuid': listing_uuid_bytes,
                'catalog': inp['catalog'],
                'record_id': rec.sql_id(),
                'user_id': u.sql_id(),
                'ts_created': now,
                'ts_updated': now,
                'update_count': 0,
                'listing_data': '{}',
            })
        res['result'] = 'ok'
        return res

    def get_listing(self, inp):
        res = {}
        listing_uuid_bytes = uuid.UUID(inp['listing']).bytes
        lst = sql_row('listing', uuid=listing_uuid_bytes)
        if not(lst.exists()):
            abort(404)
        rec = sql_row('record', id=lst['record_id'])
        if not(rec.exists()):
            abort(404)
        res['data'] = json.loads(rec['data'])
        res['record_uuid'] = str(uuid.UUID(bytes=rec['uuid']))
        res['result'] = 'ok'
        return res

    def set_record(self, inp):
        res = {}
        user_uuid_bytes = uuid.UUID(inp['user']).bytes
        record_uuid_bytes = uuid.UUID(inp['record']).bytes
        u = sql_row('user', uuid=user_uuid_bytes)
        now = sql_now()
        if not(u.exists()):
            u = sql_insert('user', {
                'uuid': user_uuid_bytes,
                'ts_created': now,
                'ts_updated': now,
            })
        r = sql_row('record', user_id=u.sql_id(), uuid=record_uuid_bytes)
        if r.exists():
            if inp.get('remove', False):
                r.delete()
            else:
                r.update({
                    'data': json.dumps(inp['data']),
                    'ts_updated': now,
                })
        else:
            r = sql_insert('record', {
                'user_id': u.sql_id(),
                'uuid': record_uuid_bytes,
                'data': json.dumps(inp['data']),
                'ts_created': now,
                'ts_updated': now,
            })
        res['result'] = 'ok'
        return res

    def get_record(self, inp):
        res = {}
        user_uuid_bytes = uuid.UUID(inp['user']).bytes
        record_uuid_bytes = uuid.UUID(inp['record']).bytes
        u = sql_row('user', uuid=user_uuid_bytes)
        if not(u.exists()):
            abort(404)
        r = sql_row('record', user_id=u.sql_id(), uuid=record_uuid_bytes)
        if not(r.exists()):
            abort(404)
        res['data'] = json.loads(r['data'])
        res['result'] = 'ok'
        return res
 
    def sync_solana_catalog(self, catalog=None):
        if not(catalog):
            raise Exception('Catalog not specified')
        url = app.config['SOLANA_TRACKER'] + 'listing_collection'
        cat = CATALOGS[catalog]
        rq = requests.post(url, json={'catalog': cat})
        if rq.status_code == 200:
            res['result'] = 'ok'
        else:
            res['result'] = 'error'
            res['error'] = rq.text
        return res
        
    def post_solana_listing(self, listing):
        uid = 2
        cat_hash = based58.b58decode(listing['category'].encode('utf8'))
        uuid_bytes = uuid.UUID(listing['uuid']).bytes
        nsql.begin()
        lock = sql_row('listing_lock',
            catalog_id=listing['catalog'],
            category_hash=cat_hash,
            owner=listing['owner'],
            uuid=uuid_bytes,
        )
        if not(lock.exists()):
            return
        spec = sql_row('listing_spec',
            catalog_id=listing['catalog'],
            category_hash=cat_hash,
            owner=listing['owner'],
        )
        if not(spec.exists()):
            return
        print(spec['listing_data'])
        filters = [None, None, None]
        for i in range(len(listing['locality'])):
            filters[i] = based58.b58decode(listing['locality'][i].encode('utf8'))
        try:
            lock.delete()
            spec.delete()
            sql_insert('listing_posted', {
                'listing_account': listing['account'],
                'listing_idx': listing['listing_idx'],
                'owner': listing['owner'],
                'uuid': uuid_bytes,
                'catalog_id': listing['catalog'],
                'category_hash': cat_hash,
                'filter_by_1': filters[0],
                'filter_by_2': filters[1],
                'filter_by_3': filters[2],
                'label': listing['label'],
                'latitude': listing['latitude'],
                'longitude': listing['longitude'],
                'detail': json.dumps(listing['detail']),
                'attributes': json.dumps(listing['attributes']),
                'update_count': listing['update_count'],
                'update_ts': datetime.fromisoformat(listing['update_ts']).strftime("%F %T"),
                'deleted_ts': None,
                'deleted': False,
            })
            record = sql_insert('record', {
                'user_id': uid,
                'uuid': uuid.uuid4().bytes,
                'ts_created': sql_now(),
                'ts_updated': sql_now(),
                'data': '{}',
            })
            sql_insert('listing', {
                'catalog': listing['catalog'],
                'user_id': uid,
                'record_id': record.sql_id(),
                'uuid': uuid_bytes,
                'update_count': listing['update_count'],
                'listing_data': '{}',
                'ts_created': sql_now(),
                'ts_updated': sql_now(),
            })
            nsql.commit()
        except Exception as e:
            nsql.rollback()
            raise e

    def remove_solana_listing(self, inp):
        rc = sql_row('listing_posted', listing_account=inp['listing'])
        if rc.exists():
            rc.update({
                'deleted_ts': sql_now(),
                'deleted': True,
            })

