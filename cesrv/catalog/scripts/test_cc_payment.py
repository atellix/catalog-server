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
order_data = {
    'amount': '126.59',
    'order_code': 'ABC',
}
payment_data = {
    'card': {
        'cardNumber': '4263982640269299',
        'cardExpires': '02/26',
        'cardSecurityCode': '777',
    },
    'billing': {
        'firstName': 'John',
        'lastName': 'Snow',
        'address': '123 Front St',
        'city': 'Columbus',
        'region': 'OH',
        'postcode': '45056',
    },
    'shipping': {
        'phone': '+13203434433',
        'email': 'johnsnow2@thenorth.com',
        'firstName': 'John',
        'lastName': 'Snow',
        'address': '123 Front St',
        'city': 'Columbus',
        'region': 'OH',
        'postcode': '45056',
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

payment_data['payment_uuid'] = order(order_data)
payment_data['card']['cardExpires'] = '02/22'
payment(payment_data)

payment_data['card']['cardExpires'] = '02/27'
payment(payment_data)

