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
    print(api_key)
    response = requests.post(url, auth=('api', api_key), json={
        'audience': 'atellix-client',
    })
    return response.json()

token = get_token(ATELLIXPAY_API_KEY)
pprint.pprint(token)

