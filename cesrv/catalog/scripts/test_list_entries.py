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

url = 'https://cat-dev1.atellix.net/api/catalog/listing/824adbab-047f-45d2-b635-6cf2cbfd19d0'
data = {
    'command': 'get_listing_entries',
}
response = requests.post(url, json=data)
pprint.pprint(response.json())

