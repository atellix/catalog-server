#!/usr/bin/env python3.10

import os
import uuid
import json
import math
import pprint
import struct
import based58
import aiohttp
import asyncio
from sanic import Sanic
from sanic.response import json as jsonify
from bitsets import bitset
from decimal import Decimal
from datetime import datetime
from dotenv import load_dotenv
from Crypto.Hash import SHAKE128
from urllib.parse import unquote
from asyncstdlib import enumerate
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import MemcmpOpts, DataSliceOpts
from solana.rpc.websocket_api import connect, RpcTransactionLogsFilterMentions
from solders.pubkey import Pubkey
from anchorpy import Program, Provider, Wallet, Context, Idl, EventParser
from anchorpy.program.common import translate_address
from catalog_client.accounts import CatalogEntry, CatalogUrl

load_dotenv('../.env')

CATALOG_ENTRY = '7gFhATbQH92' # base58 account prefix
CATALOG_ENTRY_BYTES = based58.b58decode(CATALOG_ENTRY.encode('utf8'))
SOLANA_WS = 'wss' + os.environ['SOLANA_RPC'][5:]
client = AsyncClient(os.environ['SOLANA_RPC'])
app = Sanic(name='solana_tracker')

def get_program(program_id, provider, idl_file):
    with open(idl_file) as f:
        idl = Idl.from_json(f.read())
    return Program(idl, translate_address(program_id), provider)

def get_hash(val):
    shake = SHAKE128.new()
    shake.update(val.encode('utf8'))
    return int.from_bytes(shake.read(16), 'big')

def decode_attributes(val):
    attribs = bitset('attribs', (
        'InPerson',
        'LocalDelivery',
        'OnlineDownload',
    ))
    attrib_set = {}
    for i in list(attribs.fromint(val)):
        attrib_set[i] = True
    return attrib_set

async def lookup_uri(uri_hash):
    url = os.environ['CATALOG_SERVER'] + 'uri/' + based58.b58encode(uri_hash).decode('utf8')
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.text()
            else:
                raise Exception('Invalid URI hash: ' + based58.b58encode(uri_hash).decode('utf8'))

async def sync_listing(listing):
    url = os.environ['CATALOG_SERVER'] + 'system'
    async with aiohttp.ClientSession() as session:
        inp = {
            'command': 'sync_listing',
            'listing': listing,
        }
        async with session.post(url, json=inp) as response:
            if response.status == 200:
                return await response.json()
            else:
                err = await response.text()
                raise Exception('Request failed: ' + err)

async def decode_url(client, ldata, entry):
    ud = await CatalogUrl.fetch(client, Pubkey.from_string(entry))
    udt = ud.to_json()
    if udt['url_expand_mode'] == 0:
        return udt['url']
    elif udt['url_expand_mode'] == 1:
        url = udt['url']
        entry_uuid = str(uuid.UUID(int=int(ldata['uuid'])))
        return url + entry_uuid
    elif udt['url_expand_mode'] == 2:
        return unquote(udt['url'])

async def decode_listing(ldata, defer_lookups=False):
    #pprint.pprint(ldata)
    attrs = decode_attributes(ldata['attributes'])
    label = await decode_url(client, ldata, ldata['label_url'])
    detail = json.loads(await decode_url(client, ldata, ldata['detail_url']))
    lat = None
    lon = None
    if abs(int(ldata['latitude'])) < 2000000000 and abs(int(ldata['longitude'])) < 2000000000:
        lat = Decimal(int(ldata['latitude']) / (10**7))
        lon = Decimal(int(ldata['longitude']) / (10**7))
    # TODO: Use redis cache for uris
    if defer_lookups:
        category_uri = based58.b58encode(ldata['category'].to_bytes(16, byteorder='big')).decode('utf8')
    else:
        category_uri = await lookup_uri(ldata['category'].to_bytes(16, byteorder='big'))
    locality = []
    for i in range(3):
        if ldata['filter_by'][i] > 0:
            if defer_lookups:
                locality.append(based58.b58encode(ldata['filter_by'][i].to_bytes(16, byteorder='big')).decode('utf8'))
            else:
                locality.append(await lookup_uri(ldata['filter_by'][i].to_bytes(16, byteorder='big')))
    rec = {
        'category': category_uri,
        'locality': locality,
        'url': await decode_url(client, ldata, ldata['listing_url']),
        'uuid': str(uuid.UUID(int=int(ldata['uuid']))),
        'label': label,
        'detail': detail,
        'latitude': lat,
        'longitude': lon,
        'owner': ldata['owner'],
        'attributes': attrs,
        'update_count': int(ldata['update_count']),
        'update_ts': datetime.fromtimestamp(int(ldata['update_ts'])).strftime("%F %TZ"),
        'listing_idx': ldata['listing_idx'],
    }
    return rec

@app.post('/listing')
async def get_listing(request):
    inp = request.json
    listing = await CatalogEntry.fetch(client, Pubkey.from_string(inp['account']))
    #print(listing)
    if listing is None:
        return jsonify({'result': 'error', 'error': 'Listing not found'}, status=404)
    ldata = listing.to_json()
    res = await decode_listing(ldata, defer_lookups=inp.get('defer_lookups', False))
    res['result'] = 'ok'
    return jsonify(res)

@app.post('/listing_collection')
async def get_listing_collection(request):
    inp = request.json
    program_id = Pubkey.from_string(os.environ['CATALOG_PROGRAM'])
    memcmp_opts = MemcmpOpts(offset=0, bytes=CATALOG_ENTRY) # CatalogListing
    filters = [memcmp_opts]
    if 'catalog' in inp:
        catalog = based58.b58encode(int(inp['catalog']).to_bytes(8, 'big')).decode('utf8')
        memcmp_opts2 = MemcmpOpts(offset=24, bytes=catalog)
        filters.append(memcmp_opts2)
    acts = await client.get_program_accounts(program_id, encoding='base64', filters=filters)
    acct_list = []
    for act in acts.value:
        #print(act.pubkey)
        acct_list.append(str(act.pubkey))
    res = {}
    res['collection'] = acct_list
    res['result'] = 'ok'
    return jsonify(res)

async def program_message(app, msg):
    try:
        act = msg[0].result.value.account
        if act.data[:8] == CATALOG_ENTRY_BYTES:
            listing = CatalogEntry.decode(act.data)
            ldata = listing.to_json()
            res = await decode_listing(ldata, defer_lookups=True)
            app.add_task(sync_listing(res))
    except Exception as e:
        print(e)

async def program_listener(app):
    async with connect(SOLANA_WS) as websocket:
        program_id = Pubkey.from_string(os.environ['CATALOG_PROGRAM'])
        await websocket.program_subscribe(program_id, commitment='confirmed', encoding='base64')
        recv_data = await websocket.recv()
        subscription_id = recv_data[0].result
        print('Program Subscription: program:{} subscr_id:{}'.format(os.environ['CATALOG_PROGRAM'], subscription_id))
        async for idx, msg in enumerate(websocket):
            await program_message(app, msg)

def event(evt):
    print(evt)

async def event_listener(app):
    async with connect(SOLANA_WS) as websocket:
        program_id = Pubkey.from_string(os.environ['CATALOG_PROGRAM'])
        provider = Provider(client, Wallet.dummy())
        program = get_program(program_id, provider, 'idl/catalog.json')
        evparse = EventParser(program_id=program_id, coder=program.coder)
        await websocket.logs_subscribe(filter_=RpcTransactionLogsFilterMentions(program_id), commitment='confirmed')
        recv_data = await websocket.recv()
        subscription_id = recv_data[0].result
        print('Event Subscription: program:{} subscr_id:{}'.format(os.environ['CATALOG_PROGRAM'], subscription_id))
        async for idx, msg in enumerate(websocket):
            print(msg[0])
            evparse.parse_logs(msg[0].result.value.logs, event)

@app.listener('after_server_start')
def create_solana_websocket(app, loop):
    app.add_task(program_listener(app))
    app.add_task(event_listener(app))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)

