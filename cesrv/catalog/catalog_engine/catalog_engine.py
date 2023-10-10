import re
import json
import uuid
import borsh
import pprint
import base64
import random
import based58
import krock32
import secrets
import requests
import typesense
import canonicaljson
import urllib.parse
from rdflib import Graph, URIRef
from flask import abort, current_app as app, g, session
from borsh import types
from blake3 import blake3
from datetime import datetime, timedelta
from Crypto.Hash import SHAKE128
from solders.pubkey import Pubkey
from solders.keypair import Keypair

from note.sql import *
from note.logging import *
from catalog_engine.rdf_data import DataCoder
from catalog_engine.backend.vendure_backend import VendureBackend
from .catalog_data import CatalogData, CATALOGS
from .catalog_user import CatalogUser
from .catalog_cart import CatalogCart
from .sync_solana import SyncSolana
from .sync_entries import SyncEntries

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

def sql_transaction(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        nsql.begin()
        try:
            result = function(*args, **kwargs)
            nsql.commit()
        except Exception as e:
            nsql.rollback()
            raise e
        return result
    return wrapper

class CatalogEngine():
    def __init__(self):
        self.obj_schema = app.config['CATALOG_SCHEMA']

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

    def sync_listings(self, data):
        res = {}
        user = g.user
        catalog_id = CATALOGS[data['catalog']]
        bkq = nsql.table('user_backend').get(
            select = ['id', 'backend_name', 'config_data'],
            where = {
                'user_id': user.sql_id(),
            },
            order = 'id asc',
        )
        listing_add = []
        listing_remove = []
        seen_add = {}
        seen_remove = {}
        for bk in bkq:
            backend = bk['backend_name']
            bkdata = json.loads(bk['config_data'])
            if backend == 'vendure':
                gr = Graph()
                #log_warn(user['merchant_data'])
                gr.parse(data=user['merchant_data'], format='json-ld')
                vb = VendureBackend(bk['id'], gr, URIRef(user['merchant_uri']), bkdata['vendure_url'])
                listings = vb.sync_listings(user, catalog_id, bk['id'], root_id=bkdata.get('root_collection', '1'))
                if len(listings['listing_add']) > 0:
                    for l in listings['listing_add']:
                        if l['category'] not in seen_add:
                            seen_add[l['category']] = True
                            listing_add.append(l)
                if len(listings['listing_remove']) > 0:
                    for l in listings['listing_remove']:
                        if l not in seen_remove:
                            seen_remove[l] = True
                            listing_remove.append(l)
        res['listing_add'] = listing_add
        res['listing_remove'] = listing_remove
        log_warn('Sync Listings: {}'.format(pprint.pformat(res)))
        res['result'] = 'ok'
        return res

# cfg:
#  - catalog_program: pubkey string
#  - signer_secret: keypair string
#  - fee_account: pubkey string
#  - fee_mint: pubkey string
#  - fee_tokens: int
    def sign_listing(self, cfg, inp):
        log_warn('Sign Input: {}'.format(inp))
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
        user = g.user
        owner_pk = based58.b58encode(base64.b64decode(inp['owner'])).decode('utf8')
        if user['merchant_pk'] != owner_pk:
            raise Exception('Invalid merchant key')
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

    def sync_solana_catalog(self, catalog=None):
        if not(catalog):
            raise Exception('Catalog not specified')
        cat = CATALOGS[catalog]
        sync_solana = SyncSolana(cat, self)
        sync_solana.sync()
        res = {}
        res['result'] = 'ok'
        return res
        
    def post_solana_listing(self, listing):
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
            return False
        specs = nsql.table('listing_spec').get(
            select = ['sp.id', 'sp.listing_data', 'sp.user_id', 'sp.backend_id', 'ub.backend_name'],
            table = 'listing_spec sp, user_backend ub',
            join = ['sp.backend_id=ub.id'],
            where = {
                'sp.catalog_id': listing['catalog'],
                'sp.category_hash': cat_hash,
                'sp.owner': listing['owner'],
            },
        )
        if not(len(specs)):
            return False
        uid = specs[0]['user_id']
        listing_data = {'backend': []}
        bklist = []
        for spec in specs:
            backend_data = json.loads(spec['listing_data'])
            listing_data['backend'].append([spec['backend_name'], backend_data])
            bklist.append(spec['backend_id'])
        filters = [None, None, None]
        for i in range(len(listing['locality'])):
            filters[i] = based58.b58decode(listing['locality'][i].encode('utf8'))
        try:
            sql_insert('listing_posted', {
                'listing_account': listing['account'],
                'listing_idx': listing['listing_idx'],
                'listing_data': json.dumps(listing_data),
                'owner': listing['owner'],
                'user_id': uid,
                'internal': True,
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
            for bkid in bklist:
                sql_insert('listing_backend', {
                    'uuid': uuid_bytes,
                    'backend_id': bkid,
                })
            for spec in specs:
                nsql.table('listing_spec').delete(where={'id': spec['id']})
            lock.delete()
            nsql.commit()
        except Exception as e:
            nsql.rollback()
            raise e
        return True

    def remove_solana_listing(self, inp):
        rc = sql_row('listing_posted', listing_account=inp['listing'], deleted=False)
        if rc.exists():
            rc.update({
                'deleted_ts': sql_now(),
                'deleted': True,
            })
            # Remove entry_listing rows
            nsql.table('entry_listing').delete(
                where = {'listing_posted_id': rc.sql_id()},
            )
            return True
        return False

    def build_catalog(self, catalog=None, reindex=False, user_id=None):
        if not(catalog):
            raise Exception('Catalog not specified')
        cat = CATALOGS[catalog]
        #obj_coder = DataCoder(self.obj_schema, gr, 'http://rdf.atellix.net/uuid') # TODO: config
        whr = {
            'lp.catalog_id': cat,
            'lp.deleted': False,
            'lp.internal': True,
        }
        if user_id is not None:
            whr['lp.user_id'] = user_id
        nsql.begin()
        try:
            listings = nsql.table('listing_posted').get(
                select = ['lp.id', 'lp.uuid', 'lp.user_id', 'lp.listing_data', 'u.merchant_uri'],
                table = ['listing_posted lp', 'user u'],
                join = ['lp.user_id=u.id'],
                where = whr,
                order = 'lp.listing_idx asc',
            )
            #log_warn(listings)
            index_add = []
            entry_category = {}
            entry_index = {}
            entry_user = {}
            sql_tx = False
            for l in listings:
                l['uuid'] = str(uuid.UUID(bytes=l['uuid']))
                l['listing_data'] = json.loads(l['listing_data'])
                for i in l['listing_data']['backend']:
                    bk = i[0]
                    bkrec = sql_row('user_backend', user_id=l['user_id'], backend_name=bk)
                    if not(bkrec.exists()):
                        raise Exception('Invalid backend: {} for user: {}'.format(bk, l['user_id']))
                    nsql.commit()
                    nsql.begin()
                    sync_entries = SyncEntries(bkrec, l, i[1], reindex)
                    sync_entries.sync()
                    sync_entries.finalize()
                    nsql.commit()
                    nsql.begin()
            pgwhr = 'NOT EXISTS (SELECT * FROM entry_listing el WHERE el.entry_id=e.id)'
            if user_id is not None:
                pgwhr = [{'e.user_id': user_id}, 'AND', pgwhr]
            purge = nsql.table('entry').get(
                select = ['e.id'],
                table = 'entry e',
                where = pgwhr,
            )
            for pg in purge:
                SyncEntries.remove_entry(pg['id'])
            nsql.commit()
        except Exception as e:
            nsql.rollback()
            raise e
        #print(gr.serialize(format='turtle'))

    def get_summary_by_category_slug(self, slug, limit, page):
        list_uuid = str(uuid.uuid4())
        ofs = (page - 1) * limit
        clist = URIRef(f'http://rdf.atellix.net/1.0/catalog/category.{slug}.{page}')
        entry_ct = nsql.table('category_internal').get(
            select = ['count(distinct e.entry_key) as ct'],
            table = 'category_public cp, entry_category ec, entry e',
            join = ['cp.id=ec.public_id', 'ec.entry_id=e.id'],
            where = {'cp.slug': slug},
        )[0]['ct']
        if entry_ct is None:
            entry_ct = 0
        entries = nsql.table('category_internal').get(
            select = [
                'e.external_uri', 'e.entry_key', 'e.slug', 'e.data_summary', 'e.user_id',
            ],
            table = 'category_public cp, entry_category ec, entry e',
            join = ['cp.id=ec.public_id', 'ec.entry_id=e.id'],
            where = {'cp.slug': slug},
            order = 'ec.name asc',
            limit = limit,
            offset = ofs,
            result = list,
        )
        #pprint.pprint(entries)
        product_list = []
        gr = Graph()
        users = {}
        for entry in entries:
            gr.parse(data=entry['data_summary'], format='json-ld')
            encoder = krock32.Encoder(checksum=False)
            encoder.update(entry['entry_key'])
            ident = encoder.finalize().upper()
            if entry['slug'] is not None and len(entry['slug']) > 0:
                ident = '{}-{}'.format(entry['slug'], ident)
            product_list.append({
                'id': entry['external_uri'],
                'identifier': ident,
                'type': None,
            })
            if entry['user_id'] not in users:
                users[entry['user_id']] = True
                urc = sql_row('user', id=entry['user_id'])
                gr.parse(data=urc['merchant_data'], format='json-ld')
        spec = {
            'id': clist,
            'uuid': list_uuid,
            'type': 'IOrderedCollection',
            'memberList': product_list,
        }
        coder = DataCoder(self.obj_schema, gr, spec['id'])
        coder.encode_rdf(spec)
        return {
            'graph': gr, 
            'uuid': list_uuid, 
            'count': entry_ct,
            'page': page,
            'limit': limit,
        }

    def get_summary_by_search(self, search, limit, page):
        ofs = (page - 1) * limit
        list_uuid = str(uuid.uuid4())
        search_enc = urllib.parse.quote_plus(search)
        clist = URIRef(f'http://rdf.atellix.net/1.0/catalog/search.{search_enc}')
        product_list = []
        cd = CatalogData()
        sres = cd.product_search({
            'q': search,
        })
        entry_ct = nsql.table('category_internal').get(
            select = ['count(distinct e.entry_key) as ct'],
            table = 'entry e',
            where = {'e.id': sql_in(sres)},
        )[0]['ct']
        if entry_ct is None:
            entry_ct = 0
        entries = nsql.table('category_internal').get(
            select = ['e.id', 'e.external_uri', 'e.entry_key', 'e.slug', 'e.data_summary', 'e.user_id'],
            table = 'entry e',
            where = {'e.id': sql_in(sres)},
            order = 'e.id asc',
            limit = limit,
            offset = ofs,
            result = list,
        )
        users = {}
        results = {}
        gr = Graph()
        for entry in entries:
            gr.parse(data=entry['data_summary'], format='json-ld')
            encoder = krock32.Encoder(checksum=False)
            encoder.update(entry['entry_key'])
            ident = encoder.finalize().upper()
            if entry['slug'] is not None and len(entry['slug']) > 0:
                ident = '{}-{}'.format(entry['slug'], ident)
            results[str(entry['id'])] = {
                'id': entry['external_uri'],
                'identifier': ident,
                'type': None,
            }
            if entry['user_id'] not in users:
                users[entry['user_id']] = True
                urc = sql_row('user', id=entry['user_id'])
                gr.parse(data=urc['merchant_data'], format='json-ld')
        # Return with order provided by the search
        for entry_id in sres:
            if entry_id in results:
                product_list.append(results[entry_id])
        spec = {
            'id': clist,
            'uuid': list_uuid,
            'type': 'IOrderedCollection',
            'memberList': product_list,
        }
        coder = DataCoder(self.obj_schema, gr, spec['id'])
        coder.encode_rdf(spec)
        return {
            'graph': gr, 
            'uuid': list_uuid, 
            'count': entry_ct,
            'page': page,
            'limit': limit,
        }

    def get_summary_by_edition(self, edition):
        list_uuid = str(uuid.uuid4())
        page = 1
        clist = URIRef(f'http://rdf.atellix.net/1.0/catalog/category_edition.{edition}.{page}')
        if edition == 'latest':
            entries = nsql.table('category_internal').get(
                select = [
                    'e.external_uri', 'e.entry_key', 'e.slug', 'e.data_summary', 'e.user_id',
                ],
                table = 'category_public cp, entry_category ec, entry e',
                join = ['cp.id=ec.public_id', 'ec.entry_id=e.id'],
                order = 'e.id desc',
                limit = 8,
                offset = 0,
                result = list,
            )
        elif edition == 'featured':
            entries = nsql.table('category_internal').get(
                select = [
                    'e.external_uri', 'e.entry_key', 'e.slug', 'e.data_summary', 'e.user_id',
                ],
                table = 'category_public cp, entry_category ec, entry e',
                join = ['cp.id=ec.public_id', 'ec.entry_id=e.id'],
                limit = 100,
                offset = 0,
                result = list,
            )
            entries = random.sample(entries, min(8, len(entries)))
        else:
            raise Exception(f'Unknown edition: {edition}')
        #pprint.pprint(entries)
        product_list = []
        gr = Graph()
        users = {}
        for entry in entries:
            gr.parse(data=entry['data_summary'], format='json-ld')
            encoder = krock32.Encoder(checksum=False)
            encoder.update(entry['entry_key'])
            ident = encoder.finalize().upper()
            if entry['slug'] is not None and len(entry['slug']) > 0:
                ident = '{}-{}'.format(entry['slug'], ident)
            product_list.append({
                'id': entry['external_uri'],
                'identifier': ident,
                'type': None,
            })
            if entry['user_id'] not in users:
                users[entry['user_id']] = True
                urc = sql_row('user', id=entry['user_id'])
                gr.parse(data=urc['merchant_data'], format='json-ld')
        spec = {
            'id': clist,
            'uuid': list_uuid,
            'type': 'IOrderedCollection',
            'memberList': product_list,
        }
        coder = DataCoder(self.obj_schema, gr, spec['id'])
        coder.encode_rdf(spec)
        return gr, list_uuid

    def decode_entry_key(self, slug):
        index = 0
        if '.' in slug:
            pts = slug.split('.', 2)
            slug = pts[0]
            index = int(pts[1])
        if '-' in slug:
            slug = slug.split('-')[-1]
        decoder = krock32.Decoder(strict=False, checksum=False)
        decoder.update(slug)
        entry_key = decoder.finalize()
        if len(entry_key) != 10:
            raise Exception('Invalid entry key size')
        return entry_key, index

    def get_product_by_key(self, slug, category=None):
        entry_key, index = self.decode_entry_key(slug)
        gr = Graph()
        entry = sql_row('entry', entry_key=entry_key)
        user = sql_row('user', id=entry['user_id'])
        gr.parse(data=entry['data_jsonld'], format='json-ld')
        gr.parse(data=user['merchant_data'], format='json-ld')
        entry_uuid = str(uuid.UUID(bytes=entry['uuid']))
        if category is None:
            # Get default category for entry
            cpath = nsql.table('entry_category').get(
                select = 'cp.path',
                table = 'entry_category ec, category_public cp',
                join = 'ec.public_id=cp.id',
                where = {'ec.entry_id': entry.sql_id()},
                order = 'ec.id asc',
                limit = 1,
                result = list,
            )
            category_path = json.loads(cpath[0][0])
        else:
            crc = sql_row('category_public', slug=category)
            category_path = json.loads(crc['path'])
        return gr, entry_uuid, category_path, index

    def create_user(self, data):
        user_uuid = uuid.UUID(data['uuid']).bytes
        current = sql_row('user', uuid=user_uuid)
        res = {}
        if current.exists():
            res['error'] = 'Duplicate user UUID: {}'.format(data['uuid'])
            res['result'] = 'error'
            return res
        data['uuid'] = user_uuid
        CatalogUser.create_user(data)
        res['result'] = 'ok'
        return res

    def update_user(self, data):
        CatalogUser.update_user(data)
        res = {}
        res['result'] = 'ok'
        return res

### API QUERIES
    def get_listing(self, inp):
        res = {}
        listing_uuid_bytes = uuid.UUID(inp['listing']).bytes
        lst = sql_row('listing_posted', uuid=listing_uuid_bytes, internal=True)
        if not(lst.exists()):
            abort(404)
        # TODO: Build listing data
        res['result'] = 'ok'
        return res

    def query_listings(self, inp):
        whr = {
            'lp.catalog_id': inp['catalog'],
            'lp.deleted': False,
        }
        if 'category' in inp:
            # Check if category is a public category
            pubcat = sql_row('category_public', public_uri=inp['category'])
            if pubcat.exists():
                pubq = nsql.table('category_public_internal').get(
                    select = ['u.uri_hash'],
                    table = ['category_public_internal cpi', 'category_internal ci', 'uri as u'],
                    join = ['cpi.internal_id=ci.id', 'u.uri=ci.internal_uri'],
                    where = {
                        'cpi.public_id': pubcat.sql_id(),
                    }
                )
                hashes = []
                for pr in pubq:
                    hashes.append(pr['uri_hash'])
                whr['lp.category_hash'] = sql_in(hashes)
            else:
                urc = sql_row('uri', uri=inp['category'])
                whr['lp.category_hash'] = urc['uri_hash']
        ctq = nsql.table('listing_posted').get(
            select = ['count(lp.id) as ct'],
            table = 'listing_posted lp',
            where = whr,
        )
        if len(ctq):
            ct = ctq[0]['ct']
        else:
            ct = 0
        lim = 100
        ofs = 0
        if 'take' in inp:
            take = int(inp['take'])
            if take < 1 or take > 1000:
                raise Exception('Invalid parameter value for \'take\'')
            lim = take
        if 'skip' in inp:
            skip = int(inp['skip'])
            if skip < 0:
                raise Exception('Invalid parameter value for \'skip\'')
            ofs = skip
        lq = nsql.table('listing_posted').get(
            select = [
                'lp.listing_account',
                'lp.listing_idx',
                'lp.attributes',
                '(select u.uri from uri u where u.uri_hash=lp.category_hash) as category',
                'lp.detail',
                '(select u.uri from uri u where u.uri_hash=lp.filter_by_1) as filter_by_1',
                '(select u.uri from uri u where u.uri_hash=lp.filter_by_2) as filter_by_2',
                '(select u.uri from uri u where u.uri_hash=lp.filter_by_3) as filter_by_3',
                'lp.label',
                'lp.uuid',
                'lp.latitude',
                'lp.longitude',
                'lp.longitude',
                'lp.owner',
                'lp.update_count',
                'lp.update_ts',
            ],
            table = 'listing_posted lp',
            where = whr,
            limit = lim,
            offset = ofs,
        )
        res = {}
        listings = []
        for lst in lq:
            locality = []
            for i in [1, 2, 3]:
                if lst[f'filter_by_{i}'] is not None:
                    locality.append(lst[f'filter_by_{i}'])
            lst_uuid = str(uuid.UUID(bytes=lst['uuid']))
            url = 'https://{}/api/catalog/listing/{}'.format(app.config['NGINX_HOST'], lst_uuid)
            listings.append({
                'catalog': inp['catalog'],
                'listing_account': lst['listing_account'],
                'listing_index': lst['listing_idx'],
                'category': lst['category'],
                'locality': locality,
                'url': url,
                'uuid': lst_uuid,
                'label': lst['label'],
                'detail': json.loads(lst['detail']),
                'owner': lst['owner'],
                'attributes': json.loads(lst['attributes']),
                'update_count': lst['update_count'],
                'update_ts': lst['update_ts'].strftime("%FT%TZ"),
            })
        res['count'] = ct
        res['listings'] = listings
        res['result'] = 'ok'
        return res

    def get_listing_entries(self, listing_uuid, inp):
        res = {}
        listing_uuid_bytes = uuid.UUID(listing_uuid).bytes
        lst = sql_row('listing_posted', uuid=listing_uuid_bytes, internal=True)
        if not(lst.exists()):
            abort(404)
        whr = {'el.listing_posted_id': lst.sql_id()}
        ctq = nsql.table('entry_listing').get(
            select = ['count(e.id) as ct'],
            table = ['entry_listing el', 'entry e'],
            join = ['el.entry_id=e.id'],
            where = whr,
        )
        if len(ctq):
            ct = ctq[0]['ct']
        else:
            ct = 0
        lim = 100
        ofs = 0
        if 'take' in inp:
            take = int(inp['take'])
            if take < 1 or take > 1000:
                raise Exception('Invalid parameter value for \'take\'')
            lim = take
        if 'skip' in inp:
            skip = int(inp['skip'])
            if skip < 0:
                raise Exception('Invalid parameter value for \'skip\'')
            ofs = skip
        listing_table = ['entry_listing el', 'entry e', 'user u']
        listing_join = ['el.entry_id=e.id', 'e.user_id=u.id']
        listing_sort = 'el.entry_id'
        if 'sort' in inp:
            sort_reverse = False
            if 'reverse' in inp:
                sort_reverse = inp['reverse']
            if inp['sort'] == 'price':
                listing_table.append('entry_category ect')
                listing_join.append('e.id=ect.entry_id')
                listing_sort = 'ect.price'
            elif inp['sort'] == 'name':
                listing_table.append('entry_category ect')
                listing_join.append('e.id=ect.entry_id')
                listing_sort = 'ect.name'
            if sort_reverse:
                listing_sort = listing_sort + ' desc'
            else:
                listing_sort = listing_sort + ' asc'
        lstq = nsql.table('entry_listing').get(
            select = [
                'e.id', 'el.entry_version', 'e.slug', 'e.uuid', 'e.ts_created', 'e.ts_updated', 'e.data', 'e.slug', 'e.external_uri', 'e.entry_key', 'u.merchant_label', 'u.merchant_uri',
                '(SELECT JSON_ARRAYAGG(JSON_OBJECT(\'price\', ec.price, \'public_category\', cp.public_uri)) FROM entry_category ec, category_public cp WHERE ec.entry_id=e.id AND cp.id=ec.public_id) AS public_categories',
            ],
            table = listing_table,
            join = listing_join,
            where = whr,
            order = listing_sort,
            limit = lim,
            offset = ofs,
        )
        entries = []
        for rc in lstq:
            encoder = krock32.Encoder(checksum=False)
            encoder.update(rc['entry_key'])
            entry = {
                'id': encoder.finalize().upper(),
                'uuid': str(uuid.UUID(bytes=rc['uuid'])),
                'version': rc['entry_version'],
                'data': json.loads(rc['data']),
                'slug': rc['slug'],
                'created': rc['ts_created'],
                'updated': rc['ts_updated'],
                'uri': rc['external_uri'],
                'merchant': {
                    'name': rc['merchant_label'],
                    'url': rc['merchant_uri'],
                },
            }
            if rc['public_categories'] is not None:
                entry['public_categories'] = json.loads(rc['public_categories'])
            entries.append(entry)
        res['count'] = ct
        res['entries'] = entries
        res['result'] = 'ok'
        return res

    def build_contact(self, ctdata):
        ct = {}
        for k in ['firstName', 'lastName', 'email', 'phone', 'country', 'city', 'region', 'postcode', 'address']:
            ct[k] = ctdata.get(k, '')
        for k in ['company', 'address2']:
            if k in ctdata:
                ct[k] = ctdata[k]
        return ct

    def prepare_order(self, inp):
        log_warn('Prepare Order: {}'.format(inp))
        ct = CatalogCart()
        if len(inp['items']) < 1:
            raise Exception('No items')
        for item in inp['items']:
            last_res = ct.add_cart_item('{}.{}'.format(item['id'], item.get('variant', 0)), item.get('quantity', 1))
            g.cart = last_res['id']
        merchants = last_res['cart_items']['merchants']
        pmt_spec = {}
        for ci in last_res['cart_items']['items']:
            merchant_uri = merchants[ci['merchant']]['id']
            pmt_spec[merchant_uri] = inp['payment_method']
        shipping = self.build_contact(inp['shipping_address'])
        billing = self.build_contact(inp['billing_address'])
        spec = {
            'paymentMethod': pmt_spec,
            'shippingAddress': shipping,
            'billingAddress': billing,
        }
        ct.set_shipping({'spec': spec})
        checkout = ct.prepare_checkout({'spec': spec})
        res = {}
        cart = sql_row('client_cart', id=g.cart)
        res['uuid'] = str(uuid.UUID(bytes=cart['uuid']))
        res['payments'] = checkout['payments']
        res['result'] = 'ok'
        return res

    def iterate_category(self, parent_id, parent_url, depth):
        ctq = nsql.table('category_public').get(
            select = ['id', 'public_uri', 'path', 'slug'],
            where = {
                'parent_id': parent_id,
            },
        )
        result = []
        for r in ctq:
            path = json.loads(r['path'])
            subcat = []
            if depth > 0:
                subcat = self.iterate_category(r['id'], r['public_uri'], depth - 1)
            listcat = []
            lcq = nsql.table('category_internal').get(
                select = ['ci.internal_uri'],
                table = ['category_public_internal cpi', 'category_internal ci'],
                join = ['cpi.internal_id=ci.id'],
                where = {
                    'cpi.public_id': r['id'],
                },
                order = 'ci.internal_uri asc',
            )
            for c in lcq:
                listcat.append(c['internal_uri'])
            result.append({
                'url': r['public_uri'],
                'name': path[-1]['name'],
                'slug': r['slug'],
                'path': path,
                'parent': parent_url,
                'subcategories': subcat,
                'listing_categories': listcat,
            })
        return result

    def get_category_list(self, inp):
        res = {}
        tree = inp.get('tree', None) # TODO: alternate category trees
        base = inp.get('base', None)
        depth = inp.get('depth', 1)
        maxdepth = 10
        if depth > maxdepth:
            raise Exception(f'Depth exceeds max of {maxdepth}')
        base_id = None
        base_uri = ''
        if base is not None:
            base_rc = sql_row('category_public', public_uri=base)
            if not(base_rc.exist()):
                res['result'] = 'error'
                res['error'] = f'Base category not found: {base}'
                log_warn(res['error'])
        categories = self.iterate_category(base_id, base_uri, depth)
        res['categories'] = categories
        res['result'] = 'ok'
        return res

    def get_entries_by_search(self, inp):
        res = {}
        cat = inp.get('catalog', 'commerce')
        if cat not in CATALOGS:
            res['result'] = 'error'
            res['error'] = f'Catalog not found: {cat}'
            log_warn(res['error'])
        search = inp['query']
        cd = CatalogData()
        sres = cd.product_search({
            'q': search,
        })
        entry_ct = nsql.table('category_internal').get(
            select = ['count(distinct e.entry_key) as ct'],
            table = 'entry e',
            where = {'e.id': sql_in(sres)},
        )[0]['ct']
        if entry_ct is None:
            entry_ct = 0
        lstq = nsql.table('category_internal').get(
            select = [
                'e.id', 'el.entry_version', 'e.slug', 'e.uuid', 'e.ts_created', 'e.ts_updated', 'e.data', 'e.slug', 'e.external_uri', 'e.entry_key', 'u.merchant_label', 'u.merchant_uri',
                '(SELECT JSON_ARRAYAGG(JSON_OBJECT(\'price\', ec.price, \'public_category\', cp.public_uri)) FROM entry_category ec, category_public cp WHERE ec.entry_id=e.id AND cp.id=ec.public_id) AS public_categories',
            ],
            table = ['entry e', 'entry_listing el', 'user u'],
            where = {'e.id': sql_in(sres)},
            join = ['el.entry_id=e.id', 'e.user_id=u.id'],
            order = 'e.id asc',
            result = list,
        )
        lstids = {}
        for rc in lstq:
            lstids[str(rc['id'])] = rc
        lstout = []
        for entry_id in sres:
            if entry_id in lstids:
                lstout.append(lstids[entry_id])
        entries = []
        for rc in lstout:
            encoder = krock32.Encoder(checksum=False)
            encoder.update(rc['entry_key'])
            entry = {
                'id': encoder.finalize().upper(),
                'uuid': str(uuid.UUID(bytes=rc['uuid'])),
                'version': rc['entry_version'],
                'data': json.loads(rc['data']),
                'slug': rc['slug'],
                'created': rc['ts_created'],
                'updated': rc['ts_updated'],
                'uri': rc['external_uri'],
                'merchant': {
                    'name': rc['merchant_label'],
                    'url': rc['merchant_uri'],
                },
            }
            if rc['public_categories'] is not None:
                entry['public_categories'] = json.loads(rc['public_categories'])
            entries.append(entry)
        res['count'] = entry_ct
        res['entries'] = entries
        res['result'] = 'ok'
        return res

    def get_category_info(self, slug):
        rc = sql_row('category_public', slug=slug)
        if not(rc.exists()):
            return None
        path = json.loads(rc['path'])
        top = path[-1]
        counter = 1
        info = {
            'id': counter,
            'name': top['name'],
            'slug': top['key'],
        }
        if len(path) > 1:
            last = info
            for i in range(1, len(path)):
                j = len(path) - (i + 1)
                counter = counter + 1
                last['parent'] = {
                    'id': counter,
                    'name': path[j]['name'],
                    'slug': path[j]['key'],
                }
                last = last['parent']
        #log_warn(info)
        return info

