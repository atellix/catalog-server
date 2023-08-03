#!/usr/bin/env python3

import os
import sys
import uuid
import json
import math
import pprint
import struct
import based58
import aiohttp
import asyncio
from sanic import Sanic
from sanic.log import logger
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

#load_dotenv('.env')

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

async def system_cmd(cmd, data={}):
    url = os.environ['CATALOG_SERVER'] + 'system'
    async with aiohttp.ClientSession() as session:
        inp = {'command': cmd}
        inp.update(data)
        async with session.post(url, json=inp) as response:
            if response.status == 200:
                return await response.json()
            else:
                err = await response.text()
                raise Exception('Request failed: ' + err)

async def decode_url(client, ldata, entry):
    for tries in range(5):
        ud = await CatalogUrl.fetch(client, Pubkey.from_string(entry))
        if ud is not None:
            break
        await asyncio.sleep(3)
    if ud is None:
        raise Exception('Unable to fetch URL: {}'.format(entry))
    #logger.info('Decode URL: {} Found: {}'.format(entry, ud))
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
    #logger.info('Decode Listing: {}'.format(ldata))
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
        'catalog': ldata['catalog'],
        'listing_idx': ldata['listing_idx'],
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
        'update_ts': datetime.fromtimestamp(int(ldata['update_ts'])).strftime("%FT%T+00:00"),
    }
    return rec

@app.post('/listing')
async def get_listing(request):
    inp = request.json
    listing = await CatalogEntry.fetch(client, Pubkey.from_string(inp['account']))
    #logger.info(listing)
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
    memcmp_opts = MemcmpOpts(offset=0, bytes=CATALOG_ENTRY_BYTES) # CatalogListing
    filters = [memcmp_opts]
    if 'catalog' in inp:
        catalog = based58.b58encode(int(inp['catalog']).to_bytes(8, 'little')).decode('utf8')
        memcmp_opts2 = MemcmpOpts(offset=24, bytes=catalog)
        filters.append(memcmp_opts2)
    #logger.info(filters)
    acts = await client.get_program_accounts(program_id, encoding='base64', filters=filters)
    acct_list = []
    for act in acts.value:
        #logger.info(based58.b58encode(act.account.data[:8]))
        #logger.info(act.pubkey)
        acct_list.append(str(act.pubkey))
    res = {}
    ct = len(acct_list)
    logger.info(f'Listing collection: {inp} count: {ct}')
    res['collection'] = acct_list
    res['result'] = 'ok'
    return jsonify(res)

async def post_listing(res):
    try:
        await system_cmd('post_listing', {
            'listing': res,
        })
        logger.info('Posted Listing: ' + res['account'])
    except Exception as e:
        logger.info(e)

async def remove_listing(sig, evtdata):
    try:
        lrec = {
            'sig': str(sig),
            'catalog': evtdata.catalog,
            'listing_idx': evtdata.listing_idx,
            'listing': str(evtdata.listing),
            'user': str(evtdata.user),
        }
        await system_cmd('remove_listing', lrec)
        logger.info('Removed Listing: ' + str(evtdata.listing))
    except Exception as e:
        logger.info(e)

async def program_message(app, msg):
    try:
        #logger.info(pprint.pformat(msg[0].result.value.account))
        act = msg[0].result.value.account
        if act.data[:8] == CATALOG_ENTRY_BYTES:
            listing = CatalogEntry.decode(act.data)
            #logger.info(act.data)
            #logger.info(listing)
            #logger.info()
            ldata = listing.to_json()
            res = await decode_listing(ldata, defer_lookups=True)
            res['account'] = str(msg[0].result.value.pubkey)
            app.add_task(post_listing(res))
    except Exception as e:
        logger.info(e)

async def send_ping(ws):
    while True:
        await asyncio.sleep(10)
        pong = ws.ping()
        try:
            await asyncio.wait_for(pong, timeout=2.0)
            logger.info('Ping-pong succeeded')
        except TimeoutError:
            logger.info('Ping-pong failed')
            return

async def program_listener(app):
    async with connect(SOLANA_WS) as websocket:
        program_id = Pubkey.from_string(os.environ['CATALOG_PROGRAM'])
        await websocket.program_subscribe(program_id, commitment='confirmed', encoding='base64')
        recv_data = await websocket.recv()
        subscription_id = recv_data[0].result
        logger.info('Program Subscription: program:{} subscr_id:{}'.format(os.environ['CATALOG_PROGRAM'], subscription_id))
        app.add_task(send_ping(websocket))
        async for idx, msg in enumerate(websocket):
            await program_message(app, msg)

def event_processor(sig, evt):
    #logger.info(evt)
    if evt.name == 'RemoveListingEvent':
        app.add_task(remove_listing(sig, evt.data))

async def event_listener(app):
    async with connect(SOLANA_WS) as websocket:
        program_id = Pubkey.from_string(os.environ['CATALOG_PROGRAM'])
        provider = Provider(client, Wallet.dummy())
        program = get_program(program_id, provider, 'idl/catalog.json')
        evparse = EventParser(program_id=program_id, coder=program.coder)
        await websocket.logs_subscribe(filter_=RpcTransactionLogsFilterMentions(program_id), commitment='confirmed')
        recv_data = await websocket.recv()
        subscription_id = recv_data[0].result
        logger.info('Event Subscription: program:{} subscr_id:{}'.format(os.environ['CATALOG_PROGRAM'], subscription_id))
        async for idx, msg in enumerate(websocket):
            def event_proc(evt):
                event_processor(msg[0].result.value.signature, evt)
            evparse.parse_logs(msg[0].result.value.logs, event_proc)

@app.listener('after_server_start')
def create_solana_websocket(app, loop):
    app.add_task(program_listener(app))
    app.add_task(event_listener(app))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get('SOLANA_TRACKER_PORT', 8000)))

