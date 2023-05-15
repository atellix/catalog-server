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

base_fields = [
    {'name': 'uri', 'type': 'string'},
    {'name': 'name', 'type': 'string'},
    {'name': 'tree', 'type': 'string', 'index': False, 'optional': True},
    {'name': 'path', 'type': 'string[]'},
    {'name': 'parent', 'type': 'string', 'optional': True},
    {'name': 'description', 'type': 'string', 'optional': True},
]

for sc in [
    'category_commerce',
    'category_event',
    'category_realestate',
]:
    schema = {
        'name': sc,
        'fields': base_fields,
    }
    tscl.collections[sc].delete()
    tscl.collections.create(schema)

print('Done')

