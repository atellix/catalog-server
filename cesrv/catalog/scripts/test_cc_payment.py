#!/usr/bin/env python3
import os
import sys
sys.path.append('..')

import json
import requests
from dotenv import load_dotenv
from rdflib import Graph, URIRef
from util import *

load_dotenv('.env')

order_url = 'https://atx2.atellix.net/api/payment_card/v1/authorizenet/order'
payment_url = 'https://atx2.atellix.net/api/payment_card/v1/authorizenet/payment'
data = {
    'amount': '126.58',
    'order_code': 'ABC',
    'card': {
        'number': '4263982640269299',
        'exp_month': '02',
        'exp_year': '2026',
        'security_code': '777',
    },
    'billing': {
        'first_name': 'John',
        'last_name': 'Snow',
        'phone': '+13203434433',
        'email': 'johnsnow@thenorth.com',
        'address': '123 Front St',
        'city': 'Columbus',
        'state': 'OH',
        'zip': '45056',
    },
    'shipping': {
        'first_name': 'John',
        'last_name': 'Snow',
        'address': '123 Front St',
        'city': 'Columbus',
        'state': 'OH',
        'zip': '45056',
    }
}

def order(data):
    response = requests.post(order_url, json={
        'amount': data['amount'],
        'order_code': data['order_code'],
    }, auth=('api', os.environ['ATELLIXPAY_API_KEY']))
    print(response.status_code)
    if response.status_code != 200:
        print(response.content)
    else: 
        return response.json()['payment_uuid']

def payment(data):
    response = requests.post(payment_url, json=data, auth=('api', os.environ['ATELLIXPAY_API_KEY']))
    print(response.status_code)
    if response.status_code != 200:
        print(response.content)
    else: 
        print(response.json())

data['payment_uuid'] = order(data)
payment(data)
