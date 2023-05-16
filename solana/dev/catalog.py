#!/usr/bin/env python3.10

import uuid
import json
import math
import struct
import based58
import asyncio
from bitsets import bitset
from decimal import Decimal
from datetime import datetime
from Crypto.Hash import SHAKE128
from urllib.parse import unquote
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import MemcmpOpts
from solders.pubkey import Pubkey
from anchorpy import Program, Provider, Wallet, Context, Idl
from anchorpy.program.common import translate_address
from catalog_client.accounts import CatalogEntry, CatalogUrl

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

async def main():
    client = AsyncClient("https://api.devnet.solana.com")
    provider = Provider(client, Wallet.dummy())
    program_id = Pubkey.from_string('CTLGp9JpcXCJZPqdn2W73c74DTsCTS8EFEedd7enU8Mv')
    program = get_program(program_id, provider, 'idl/catalog.json')
    #print(f'Wallet: {provider.wallet.public_key}')

    category_uri = None
    memcmp_opts = MemcmpOpts(offset=32, bytes='8uD5gwghxcqJw4VnH72v3h')
    acts = await client.get_program_accounts(program_id, encoding='base64', filters=[memcmp_opts])
    for act in acts.value:
        print(act.pubkey)
        listing = await CatalogEntry.fetch(client, act.pubkey)
        ldata = listing.to_json()
        lat = None
        lon = None
        if abs(int(ldata['latitude'])) < 2000000000 and abs(int(ldata['longitude'])) < 2000000000:
            lat = Decimal(int(ldata['latitude']) / (10**7))
            lon = Decimal(int(ldata['longitude']) / (10**7))
        attrs = decode_attributes(ldata['attributes'])
        rec = {
            'category': category_uri,
            'locality': [],
            'url': await decode_url(client, ldata, ldata['listing_url']),
            'uuid': str(uuid.UUID(int=int(ldata['uuid']))),
            'label': await decode_url(client, ldata, ldata['label_url']),
            'detail': await decode_url(client, ldata, ldata['detail_url']),
            'latitude': lat,
            'longitude': lon,
            'owner': ldata['owner'],
            'attributes': attrs,
            'update_count': int(ldata['update_count']),
            'update_ts': datetime.fromtimestamp(int(ldata['update_ts'])).strftime("%F %T"),
        }
        print(rec)
        #print(get_hash('http://schema.org/Event'))
    #await program.close()

asyncio.run(main())

