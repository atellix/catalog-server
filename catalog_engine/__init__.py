import json
import uuid
import borsh
import base64
import krock32
from flask import abort
from borsh import types
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from Crypto.Hash import SHAKE128

from note.sql import *

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

# TODO: database this
CATALOGS = { 'commerce': 0 }

def to_byte_array(b64_string):
    byte_string = base64.b64decode(b64_string)
    return [int(b) for b in byte_string]

def to_text_account(cfg, text_string, fill_mode=0):
    shake = SHAKE128.new()
    shake.update(text_string.encode('utf8'))
    shake_hash = shake.read(16)
    seeds = [bytes([fill_mode]), shake_hash]
    pda = Pubkey.find_program_address(seeds, Pubkey.from_string(cfg['catalog_program']))
    #print(text_string)
    #print(str(pda[0]))
    return [int(b) for b in bytes(pda[0])]

class CatalogData():
    def uri_hash_bytes(self, uri):
        shake = SHAKE128.new()
        shake.update(uri.encode('utf8'))
        return shake.read(16)

    def store_uri_hash(self, uri):
        uri_hash = self.uri_hash_bytes(uri)
        try:
            sql_insert('uri', {
                'uri_hash': uri_hash,
                'uri': uri,
            })
        except Exception as e:
            pass

class CatalogEngine():
    def __init__(self):
        pass

# cfg:
#  - catalog_program: pubkey string
#  - signer_secret: keypair string
#  - fee_account: pubkey string
#  - fee_mint: pubkey string
#  - fee_tokens: int
    def sign_listing(self, cfg, inp):
        listing_uuid = uuid.uuid4()
        listing_data = {
            'uuid': listing_uuid.int,
            'catalog': CATALOGS[inp['catalog']],
            'category': int(inp['category']),
            'filter_by_1': int(inp['filter_by_1']),
            'filter_by_2': int(inp['filter_by_2']),
            'filter_by_3': int(inp['filter_by_3']),
            'attributes': inp['attributes'],
            'latitude': to_byte_array(inp['latitude']),
            'longitude': to_byte_array(inp['longitude']),
            'owner': to_byte_array(inp['owner']),
            'listing_url': to_text_account(cfg, inp['listing_url']['text'], inp['listing_url']['expand']),
            'label_url': to_text_account(cfg, inp['label_url']['text'], inp['label_url']['expand']),
            'detail_url': to_text_account(cfg, inp['detail_url']['text'], inp['detail_url']['expand']),
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
 
class CatalogBackend:
    pass
