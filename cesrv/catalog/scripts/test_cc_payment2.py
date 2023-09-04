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

order_url = 'http://data.atellix.net:3000/payments/authorizenet'
#order_url = 'http://data.atellix.net:3000/payments/atellixpay'
data = {
    'event': 'payment_request',
    'amount': '126.58',
    'order_code': 'ABC',
}

def order(data):
    response = requests.post(order_url, data={
        'event': data['event'],
        'amount': data['amount'],
        'order_id': data['order_code'],
    })
    print(response.status_code)
    if response.status_code != 200:
        print(response.content)
    else: 
        return response.json()

print(order(data))

