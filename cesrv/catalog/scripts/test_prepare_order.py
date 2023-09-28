#!/usr/bin/env python3
import os
import sys
sys.path.append('..')

import json
import pprint
import requests
from dotenv import load_dotenv
from rdflib import Graph, URIRef
from util import *

load_dotenv('.env')

url = 'https://cat-dev1.atellix.net/api/catalog/order'
data = {
    'command': 'prepare_order',
    'payment_method': 'atellixpay',
    'items': [
        {'id': 'N1SPZ9Z9XX78V86M'},
        {'id': 'DZYPSEKZ8Y70WGE8'},
    ],
}
response = requests.post(url, json=data)
pprint.pprint(response.json())

