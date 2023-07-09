#!/usr/bin/env python3

import os
import pprint
import typesense
from dotenv import load_dotenv

load_dotenv('../.env')

tscl = typesense.Client({
    'nodes': [{
        'host': os.environ['TYPESENSE_HOST'],
        'port': os.environ['TYPESENSE_PORT'],
        'protocol': os.environ['TYPESENSE_PROTOCOL'],
    }],
    'api_key': os.environ['TYPESENSE_API_KEY'],
    'connection_timeout_seconds': 10,
})

search_parameters = {
    'q': 'lawn garden equipment and tools',
    'query_by': 'name',
}
res = tscl.collections['category_commerce'].documents.search(search_parameters)
seen = {}
for r in res['hits']:
    if r['document']['uri'] in seen:
        continue
    seen[r['document']['uri']] = True
    print(r['document']['uri'])
    print(r['document']['tree'])
    print(r['document']['name'])
    if 'description' in r['document']:
        print(r['document']['description'])
    print()

