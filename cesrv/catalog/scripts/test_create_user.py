#!/usr/bin/env python3
import sys
sys.path.append('..')

import json
import requests
from rdflib import Graph, URIRef
from util import *

prvkey = 'atx:secret:jwk1:6Puzoio5WqXHedmVUj7T8mHAjTAiu9UJrhfrZC96xpLm:DKABn3yMrKzkXrBPuxBsQCpUR8zF14E6P4y5UEU5dUtu:6AMEnawnDFko7J3dnS3RNjQuZ3VaBZs1FoRmdedJcAYi'
prv = JWKey.from_custom(prvkey, private=True)

token = JWToken.make_token(prv, {
    'iss': 'atellix-network',
    'sub': 'catalog-admin',
    'aud': 'atellix-catalog',
})

g = Graph()
g.parse('merchant.rdf')
jsl = json.loads(g.serialize(format='json-ld'))

headers = {'Authorization': f'Bearer {token}'}
url = 'https://cat-dev1.atellix.net/api/catalog/system'
data = {
    'command': 'create_user',
    'uuid': '9643e537-1a3a-408e-9c42-5095921fb0ce',
    'label': 'SavvyCo',
    'pubkey': 'G9GUQuEKS6oJsZspUrAJ1aWFqp1SPq5tgCja4wpMueyX',
    'uri': 'https://savvyco.com/',
    'merchant_data': jsl,
    'backends': [
        ['vendure', {'vendure_url': 'https://vend1.atellix.net:3443/shop-api'}],
    ],
}
response = requests.post(url, json=data, headers=headers)
print(response.json())
