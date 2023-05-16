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
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import MemcmpOpts
from solders.pubkey import Pubkey
from anchorpy import Program, Provider, Wallet, Context, Idl
from anchorpy.program.common import translate_address
from catalog_client.accounts import CatalogEntry, CatalogUrl

load_dotenv('../.env')

API_URL='http://173.234.24.74:9500/api/catalog/'

client = AsyncClient("https://api.devnet.solana.com")
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
    url = API_URL + 'uri/' + based58.b58encode(uri_hash).decode('utf8')
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.text()
            else:
                raise Exception('Invalid URI hash: ' + based58.b58encode(uri_hash).decode('utf8'))

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

async def decode_listing(ldata):
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
    category_uri = await lookup_uri(ldata['category'].to_bytes(16, byteorder='big'))
    locality = []
    for i in range(3):
        if ldata['filter_by'][i] > 0:
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
    print(listing)
    if listing is None:
        return jsonify({'result': 'error', 'error': 'Listing not found'}, status=404)
    ldata = listing.to_json()
    res = await decode_listing(ldata)
    res['result'] = 'ok'
    return jsonify(res)

@app.post('/listing_collection')
async def get_listing_collection(request):
    inp = request.json
    program_id = Pubkey.from_string(os.environ['CATALOG_PROGRAM'])
    memcmp_opts = MemcmpOpts(offset=0, bytes='7gFhATbQH92')
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

if __name__ == '__main__':
    provider = Provider(client, Wallet.dummy())
    program_id = Pubkey.from_string('CTLG5CZje37UKZ7UvXiXy1WnJs37npJHxkYXFsEcCCc1')
    program = get_program(program_id, provider, 'idl/catalog.json')
    app.run(host="0.0.0.0", port=8000)

