#!/usr/bin/env python3

import pprint
import typesense

tscl = typesense.Client({
    'nodes': [{
        'host': '173.234.24.76',    # For Typesense Cloud use xxx.a1.typesense.net
        'port': '8108',             # For Typesense Cloud use 443
        'protocol': 'http'          # For Typesense Cloud use https
    }],
    'api_key': '86zJUXvIUzA5i7ZoqH0JKKvbn',
    'connection_timeout_seconds': 10,
})

base_fields = [
    {'name': 'id', 'type': 'int64'},
    {'name': 'uri', 'type': 'string'},
    {'name': 'name', 'type': 'string'},
    {'name': 'tree', 'type': 'string'},
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
    #tscl.collections[sc].delete()
    tscl.collections.create(schema)

print('Done')

