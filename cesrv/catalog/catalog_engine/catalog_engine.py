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
from rdflib import Graph, URIRef
from flask import abort, current_app as app
from borsh import types
from blake3 import blake3
from datetime import datetime, timedelta
from Crypto.Hash import SHAKE128
from solders.pubkey import Pubkey
from solders.keypair import Keypair

from note.sql import *
from catalog_engine.rdf_data import DataCoder
from catalog_engine.backend.vendure_backend import VendureBackend
from .catalog_data import CatalogData, CATALOGS
from .catalog_user import CatalogUser
from .sync_solana import SyncSolana

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
        eturn [int(b) for b in bytes(pda[0])]

    def sync_listings(self, data):
        res = {}
        user = CatalogUser.authorize(data['token'])
        if user is None:
            abort(403)
        catalog_id = CATALOGS[data.get('catalog', 'commerce')]
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
                gr.parse(data=user['merchant_data'], format='json-ld')
                vb = VendureBackend(gr, URIRef(user['merchant_uri']), bkdata['vendure_url'])
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
        res['result'] = 'ok'
        return res

# cfg:
#  - catalog_program: pubkey string
#  - signer_secret: keypair string
#  - fee_account: pubkey string
#  - fee_mint: pubkey string
#  - fee_tokens: int
    def sign_listing(self, cfg, inp):
        # Find category in database
        user_id = 2
        cat_hash = int(inp['category']).to_bytes(16, 'big')
        cat = nsql.table('uri').get(
            select = ['uri'],
            where = {'uri_hash': cat_hash},
        )
        if not(len(cat)):
            raise Exception('Invalid category uri')
        # TODO: Verify category in graph db
        # Find or create uuid
        user_rc = sql_row('user', id=user_id)
        owner_pk = based58.b58encode(base64.b64decode(inp['owner'])).decode('utf8')
        if user_rc['merchant_pk'] != owner_pk:
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
                'catalog_id': inp['catalog'],
                'record_id': rec.sql_id(),
                'user_id': u.sql_id(),
                'ts_created': now,
                'ts_updated': now,
                'update_count': 0,
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
            select = ['sp.listing_data', 'sp.user_id', 'sp.backend_id', 'ub.backend_name'],
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
        uid = spec[0]['user_id']
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
            for bkid in bklist:
                sql_insert('listing_backend', {
                    'uuid': uuid_bytes,
                    'backend_id': bkid,
                })
            record = sql_insert('record', {
                'user_id': uid,
                'uuid': uuid.uuid4().bytes,
                'ts_created': sql_now(),
                'ts_updated': sql_now(),
                'data': json.dumps(listing_data),
            })
            sql_insert('listing', {
                'catalog_id': listing['catalog'],
                'user_id': uid,
                'record_id': record.sql_id(),
                'uuid': uuid_bytes,
                'update_count': listing['update_count'],
                'ts_created': sql_now(),
                'ts_updated': sql_now(),
            })
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
            return True
        return False

    def build_catalog_index(self, catalog=None):
        if not(catalog):
            raise Exception('Catalog not specified')
        cat = CATALOGS[catalog]
        #obj_coder = DataCoder(self.obj_schema, gr, 'http://rdf.atellix.net/uuid') # TODO: config
        listings = nsql.table('listing_posted').get(
            select = [
                'lp.id', 'lp.uuid', 'l.user_id', 'r.data', 'u.merchant_uri',
                '(select uri from uri where uri_hash=lp.category_hash) as internal_category_uri',
            ],
            table = ['listing_posted lp', 'listing l', 'record r', 'user u'],
            join = ['lp.uuid=l.uuid', 'l.record_id=r.id', 'l.user_id=u.id'],
            where = {
                'lp.catalog_id': cat,
                'lp.deleted': False,
            },
            order = 'listing_idx asc',
        )
        seen = {}
        index_add = []
        entry_category = {}
        entry_index = {}
        entry_user = {}
        nsql.begin()
        try:
            for l in listings:
                l['uuid'] = str(uuid.UUID(bytes=l['uuid']))
                l['data'] = json.loads(l['data'])
                for i in l['data']['backend']:
                    bk = i[0]
                    if bk == 'vendure':
                        #print('Vendure', i[1])
                        gr = Graph()
                        bkrec = sql_row('user_backend', user_id=l['user_id'], backend_name=bk)
                        if not(bkrec.exists()):
                            raise Exception('Invalid backend: {} for user: {}'.format(bk, l['user_id']))
                        bkid = bkrec.sql_id()
                        backend_data = json.loads(bkrec['config_data'])
                        vb = VendureBackend(gr, URIRef(l['merchant_uri']), backend_data['vendure_url'])
                        for rc in i[1]:
                            coll = vb.get_collection(rc['collection']['slug'])
                            for prod in coll['products']:
                                #print(prod['productId'])
                                if prod['productId'] in seen:
                                    self.store_listing_entry(l['id'], seen[prod['productId']])
                                    entry_category[seen[prod['productId']]].append(l['internal_category_uri'])
                                    continue
                                data = vb.get_product_item_spec(prod)
                                entry_rcid, index_cols, entry_status = self.store_catalog_entry(
                                    l['user_id'], bkid, prod['productId'], data['id'], data
                                )
                                seen[prod['productId']] = entry_rcid
                                self.store_listing_entry(l['id'], entry_rcid)
                                entry_user[entry_rcid] = l['user_id']
                                entry_category[entry_rcid] = [l['internal_category_uri']]
                                entry_index[entry_rcid] = index_cols
                                if entry_status == 'insert' or entry_status == 'update':
                                    index_add.append([entry_rcid, data])
            #pprint.pprint(entry_category)
            for k in sorted(entry_category.keys()):
                user_id = entry_user[k]
                int_cats = entry_category[k]
                idx_data = entry_index.get(k, None)
                curr_cats = self.get_entry_categories(k)
                for ic in int_cats:
                    curr_cats = self.store_entry_category(k, user_id, ic, idx_data, curr_cats)
                # Remove extra categories
                if len(curr_cats.keys()):
                    for pc in curr_cats.keys():
                        nsql.table('entry_category').delete(where = {
                            'entry_id': k,
                            'public_id': pc,
                        })
            cd = CatalogData()
            catidx = 'catalog_' + catalog
            # TODO: turn indexing back on
            #for item in index_add:
            #    cd.index_catalog_entry(catidx, item[0], item[1])
            nsql.commit()
        except Exception as e:
            nsql.rollback()
            raise e
        #print(gr.serialize(format='turtle'))

    def get_entry_categories(self, entry_id):
        q = nsql.table('entry_category').get(
            select = ['public_id'],
            where = {'entry_id': entry_id},
        )
        cats = {}
        for r in q:
            cats[str(r['public_id'])] = True
        return cats

    def store_entry_category(self, entry_id, user_id, interal_category_uri, index_data, curr_cats):
        # TODO: cache this lookup
        pub_cats = nsql.table('category_internal').get(
            select = ['distinct cpi.public_id'],
            table = 'category_internal ci, category_public_internal cpi',
            join = ['ci.id=cpi.internal_id'],
            where = {
                'ci.internal_uri': interal_category_uri,
            },
            result = list,
        )
        # TODO: warn if no public categories found
        for pc in pub_cats:
            if str(pc[0]) in curr_cats:
                del curr_cats[str(pc[0])]
            rc = sql_row('entry_category', entry_id=entry_id, public_id=pc[0])
            if rc.exists():
                if index_data is not None:
                    rc.update(index_data)
            else:
                rec = {
                    'entry_id': entry_id,
                    'public_id': pc[0],
                    'user_id': user_id,
                }
                if index_data is not None:
                    rec.update(index_data)
                sql_insert('entry_category', rec)
        return curr_cats

    def store_listing_entry(self, listing_posted_id, entry_rcid, version=0):
        rc = sql_row('entry_listing', listing_posted_id=listing_posted_id, entry_id=entry_rcid)
        if not(rc.exists()):
            sql_insert('entry_listing', {
                'listing_posted_id': listing_posted_id,
                'entry_id': entry_rcid,
                'entry_version': version,
            })

    def json_hash(self, data, digest=True):
        enc = canonicaljson.encode_canonical_json(data)
        if digest:
            hs = blake3()
            hs.update(enc)
            return enc.decode('utf8'), hs.digest() 
        else:
            return enc.decode('utf8')

    def convert_to_slug(self, label):
        # Convert to lower case
        slug = label.lower()
        # Remove extra characters
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        # Replace spaces with '-'
        slug = re.sub(r'\s+', '-', slug)
        return slug

    def get_entry_data(self, user_id, backend_id, external_id, record_uuid=None):
        gr = Graph()
        sgr = Graph()
        urc = sql_row('user', id=user_id)
        brc = sql_row('user_backend', id=backend_id, user_id=user_id)
        backend = brc['backend_name']
        backend_data = json.loads(brc['config_data'])
        if record_uuid is None:
            record_uuid = str(uuid.uuid4())
        slug = None
        data_summary = None
        indexfield = {}
        if backend == 'vendure':
            vb = VendureBackend(gr, URIRef(urc['merchant_uri']), backend_data['vendure_url'])
            obj_list = vb.get_product_spec(external_id)
            for idx in range(len(obj_list)):
                obj = obj_list[idx]
                if idx == 0:
                    obj['uuid'] = record_uuid
                    if 'alternateName' in obj:
                        slug = obj['alternateName'].lower()
                    elif 'name' in obj:
                        slug = self.convert_to_slug(obj['name'])
                    summ = vb.summarize_product_spec(obj)
                    if 'name' in summ:
                        indexfield['name'] = summ['name']
                    if 'offers' in summ:
                        if 'price' in summ['offers'][0]:
                            indexfield['price'] = summ['offers'][0]['price']
                    # TODO: brand (to string)
                    summ_coder = DataCoder(self.obj_schema, sgr, summ['id'])
                    summ_coder.encode_rdf(summ)
                    data_summary = self.json_hash(json.loads(sgr.serialize(format='json-ld')), digest=False)
                coder = DataCoder(self.obj_schema, gr, obj['id'])
                coder.encode_rdf(obj)
        #print(gr.serialize(format='turtle'))
        jsld = json.loads(gr.serialize(format='json-ld'))
        data, data_hash = self.json_hash(jsld)
        return {
            'uuid': record_uuid,
            'data': data,
            'data_hash': data_hash,
            'data_summary': data_summary, 
            'entry_name': indexfield.get('name', None),
            'entry_brand': indexfield.get('brand', None),
            'entry_price': indexfield.get('price', None),
            'slug': slug,
        }

    def update_entry_data(self, user_id, backend_id, external_id):
        pass

    def store_entry_data(self, user_id, backend_id, external_id):
        entry_data = self.get_entry_data(user_id, backend_id, external_id)
        ts = sql_now()
        rec = sql_insert('record', {
            'user_id': user_id,
            'uuid': uuid.UUID(entry_data['uuid']).bytes,
            'data': entry_data['data'],
            'data_hash': entry_data['data_hash'],
            'data_summary': entry_data['data_summary'],
            'ts_created': ts,
            'ts_updated': ts,
        })
        return rec.sql_id(), { k: entry_data['entry_' + k] for k in ['name', 'brand', 'price'] }, entry_data['slug']

    def new_entry_key(self):
        for i in range(10):
            token = secrets.token_bytes(10)
            rc = sql_row('entry', entry_key=token)
            if not(rc.exists()):
                return token
        raise Exception('Duplicate entry keys after 10 tries')

    def store_catalog_entry(self, user_id, backend_id, entry_id, entry_uri, data):
        type_id = sql_query('SELECT entry_type_id({})'.format(sql_param()), [data['type']], list)[0][0]
        index_cols = None
        entry_status = 'exists'
        external_id = str(entry_id)
        rc = sql_row('entry', backend_id=backend_id, external_id=str(entry_id))
        if rc.exists():
            if rc['external_uri'] != entry_uri or rc['type_id'] != type_id:
                entry_status = 'update'
                rc.update({
                    'external_uri': entry_uri,
                    'type_id': type_id,
                })
            entry_data = self.get_entry_data(user_id, backend_id, external_id)
            index_cols = { k: entry_data['entry_' + k] for k in ['name', 'brand', 'price'] }
        else:
            entry_status = 'insert'
            record_id, index_cols, slug = self.store_entry_data(user_id, backend_id, external_id)
            entry_key = self.new_entry_key()
            rc = sql_insert('entry', {
                'entry_key': entry_key,
                'external_id': external_id,
                'external_uri': entry_uri,
                'user_id': user_id,
                'type_id': type_id,
                'backend_id': backend_id,
                'record_id': record_id,
                'slug': slug,
            })
        return rc.sql_id(), index_cols, entry_status

    def get_summary_by_category_slug(self, slug, edition=None):
        list_uuid = str(uuid.uuid4())
        page = 1
        clist = URIRef(f'http://rdf.atellix.net/1.0/catalog/category.{slug}.{page}')
        entries = nsql.table('category_internal').get(
            select = [
                'e.external_uri', 'e.entry_key', 'e.slug', 'r.data_summary', 'e.user_id',
            ],
            table = 'category_public cp, entry_category ec, entry e, record r',
            join = ['cp.id=ec.public_id', 'ec.entry_id=e.id', 'e.record_id=r.id'],
            where = {
                'cp.slug': slug,
            },
            order = 'ec.name asc',
            limit = 25,
            offset = 0,
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
        return gr, list_uuid

    def get_summary_by_edition(self, edition):
        list_uuid = str(uuid.uuid4())
        page = 1
        clist = URIRef(f'http://rdf.atellix.net/1.0/catalog/category_edition.{edition}.{page}')
        if edition == 'latest':
            entries = nsql.table('category_internal').get(
                select = [
                    'e.external_uri', 'e.entry_key', 'e.slug', 'r.data_summary', 'e.user_id',
                ],
                table = 'category_public cp, entry_category ec, entry e, record r',
                join = ['cp.id=ec.public_id', 'ec.entry_id=e.id', 'e.record_id=r.id'],
                order = 'e.id desc',
                limit = 8,
                offset = 0,
                result = list,
            )
        elif edition == 'featured':
            entries = nsql.table('category_internal').get(
                select = [
                    'e.external_uri', 'e.entry_key', 'e.slug', 'r.data_summary', 'e.user_id',
                ],
                table = 'category_public cp, entry_category ec, entry e, record r',
                join = ['cp.id=ec.public_id', 'ec.entry_id=e.id', 'e.record_id=r.id'],
                limit = 100,
                offset = 0,
                result = list,
            )
            entries = random.sample(entries, 8)
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
        rec = sql_row('record', id=entry['record_id'])
        user = sql_row('user', id=entry['user_id'])
        gr.parse(data=rec['data'], format='json-ld')
        gr.parse(data=user['merchant_data'], format='json-ld')
        entry_uuid = str(uuid.UUID(bytes=rec['uuid']))
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

