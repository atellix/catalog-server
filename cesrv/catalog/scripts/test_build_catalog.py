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

prvkey = os.environ['ATELLIX_ADMIN_JWK']
prv = JWKey.from_custom(prvkey, private=True)

token = JWToken.make_token(prv, {'iss': 'atellix-network', 'sub': 'catalog-admin', 'aud': 'atellix-catalog'})

headers = {'Authorization': f'Bearer {token}'}
url = 'https://cat-dev1.atellix.net/api/catalog/system'
data = {
    'command': 'build_catalog_index',
    'catalog': 'commerce',
}
response = requests.post(url, json=data, headers=headers)
print(response.json())

