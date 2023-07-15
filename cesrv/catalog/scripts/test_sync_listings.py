#!/usr/bin/env python3
import sys
sys.path.append('..')

import json
import pprint
import requests
from rdflib import Graph, URIRef

ATELLIXPAY_API_KEY = 'efe866bb31ce43c8b7aa386ae013c11f40114bdfa1f34dfe939351fdc6b1f7cc'

def get_token(api_key):
    url = 'https://atx2.atellix.net/api/auth_gateway/v1/get_token'
    response = requests.get(url, auth=('api', api_key))
    return response.json()

def sync_listings(bearer_token):
    headers = {'Authorization': f'Bearer {bearer_token}'}
    url = 'https://cat-dev1.atellix.net/api/catalog/listing'
    data = {
        'command': 'sync_listings',
        'catalog': 'commerce',
    }
    response = requests.post(url, json=data, headers=headers)
    return response.json()

token = get_token(ATELLIXPAY_API_KEY)
access_token = token['access_token']
#print(access_token)

sync_result = sync_listings(access_token)
pprint.pprint(sync_result)

