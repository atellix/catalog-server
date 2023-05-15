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

base_fields = [
    {'name': 'uri', 'type': 'string'},
    {'name': 'name', 'type': 'string'},
    {'name': 'geoname', 'type': 'string'},
    {'name': 'geoname_id', 'type': 'string'},
    {'name': 'type', 'type': 'string'},
    {'name': 'path', 'type': 'string[]'},
    {'name': 'parent', 'type': 'string', 'optional': True},
    {'name': 'country_code', 'type': 'string'},
    {'name': 'region_code', 'type': 'string', 'optional': True},
    {'name': 'postal_code', 'type': 'string', 'optional': True},
    {'name': 'location', 'type': 'geopoint', 'optional': True},
]

for sc in [
    'geo_location',
]:
    schema = {
        'name': sc,
        'fields': base_fields,
    }
    tscl.collections[sc].delete()
    tscl.collections.create(schema)

print('Done')

