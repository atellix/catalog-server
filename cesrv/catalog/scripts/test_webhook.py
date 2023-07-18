#!/usr/bin/env python3
import sys
sys.path.append('..')

import json
import pprint
import requests
from rdflib import Graph, URIRef

ATELLIXPAY_API_KEY = 'efe866bb31ce43c8b7aa386ae013c11f40114bdfa1f34dfe939351fdc6b1f7cc'

def webhook_add(api_key):
    url = 'https://atx2.atellix.net/api/payment_gateway/v1/webhook'
    response = requests.post(url, auth=('api', api_key), json={
        'webhook': 'payment_success',
        'url': 'https://vend1.atellix.net:3443/payments/atellixpay',
    })
    return response.json()

def webhook_list(api_key):
    url = 'https://atx2.atellix.net/api/payment_gateway/v1/webhook/list'
    response = requests.post(url, auth=('api', api_key), json={})
    return response.json()

res = webhook_add(ATELLIXPAY_API_KEY)
pprint.pprint(res)

res = webhook_list(ATELLIXPAY_API_KEY)
pprint.pprint(res)
#
