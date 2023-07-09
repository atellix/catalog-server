#!/usr/bin/env python3

import os
import sys
import pprint
import typesense
import usaddress
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

tags = usaddress.tag('Oxford, OH', tag_mapping={
   'Recipient': 'recipient',
   'AddressNumber': 'address1',
   'AddressNumberPrefix': 'address1',
   'AddressNumberSuffix': 'address1',
   'StreetName': 'address1',
   'StreetNamePreDirectional': 'address1',
   'StreetNamePreModifier': 'address1',
   'StreetNamePreType': 'address1',
   'StreetNamePostDirectional': 'address1',
   'StreetNamePostModifier': 'address1',
   'StreetNamePostType': 'address1',
   'CornerOf': 'address1',
   'IntersectionSeparator': 'address1',
   'LandmarkName': 'address1',
   'USPSBoxGroupID': 'address1',
   'USPSBoxGroupType': 'address1',
   'USPSBoxID': 'address1',
   'USPSBoxType': 'address1',
   'BuildingName': 'address2',
   'OccupancyType': 'address2',
   'OccupancyIdentifier': 'address2',
   'SubaddressIdentifier': 'address2',
   'SubaddressType': 'address2',
   'PlaceName': 'city',
   'StateName': 'state',
   'ZipCode': 'zip_code',
})
print(tags)
sys.exit(0)

search_parameters = {
    'q': 'marina del rey',
    'filter_by': 'type:=City && region_code:=CA',
    #'filter_by': 'type:=Region',
    #'filter_by': 'type:=Country',
    #'query_by': 'name, country_code',
    #'filter_by': 'type:=Country',
    #'query_by': 'name, country_code, region_code, postal_code',
    'query_by': 'name, country_code, region_code, postal_code',
    'per_page': 100,
}
res = tscl.collections['geo_location'].documents.search(search_parameters)
seen = {}
#print(res)
for r in res['hits']:
    if r['document']['uri'] in seen:
        continue
    seen[r['document']['uri']] = True
    print(r['document'])
    #print(r['document']['type'])
    #print(r['document']['name'])
    #if 'description' in r['document']:
        #print(r['document']['description'])
    print()

