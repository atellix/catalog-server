#!/usr/bin/env python3

import os
import sys
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

commerce_catalog_schema = {
    'name': 'catalog_commerce',
    'fields': [
        {'name': 'name', 'type': 'string' },
        {'name': 'user_id', 'type': 'int64' },
        {'name': 'entry_id', 'type': 'int64' },
        {'name': 'entry_uri', 'type': 'string' },
        {'name': 'entry_type', 'type': 'string' },
        {'name': 'description', 'type': 'string' },
        {'name': 'category', 'type': 'string[]', 'facet': True },
        {'name': '.*_facet', 'type': 'auto', 'facet': True },
    ],
}

if True:
    tscl.collections.create(commerce_catalog_schema)
    #tscl.collections['product_catalog'].delete()
    #tscl.collections['product_catalog'].update(product_catalog_schema)

