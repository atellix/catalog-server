#!/usr/bin/env python3
import sys
sys.path.append('..')

import os
import json
import requests
from dotenv import load_dotenv
from rdflib import Graph, URIRef
from util import *

load_dotenv('.env')

prvkey = os.environ['ATELLIX_ADMIN_JWK']
prv = JWKey.from_custom(prvkey, private=True)

ADMIN_JWT_CLAIMS = {'iss': 'atellix-network', 'aud': 'atellix-catalog', 'sub': 'catalog-admin'}

token = JWToken.make_token(prv, ADMIN_JWT_CLAIMS)

for i in [
    'import_uris'
    #'build_category_index'
    #'build_location_index'
]:
    print(i)
    headers = {'Authorization': f'Bearer {token}'}
    url = 'https://cat-dev1.atellix.net/api/catalog/system'
    data = {'command': i}
    response = requests.post(url, json=data, headers=headers, timeout=60 * 60 * 4)
    print(response.json())

