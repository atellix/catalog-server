#!/usr/bin/env python3

import sys
sys.path.append('..')

from util import *

pubkey = 'atx:public:jwk1:6Puzoio5WqXHedmVUj7T8mHAjTAiu9UJrhfrZC96xpLm:DKABn3yMrKzkXrBPuxBsQCpUR8zF14E6P4y5UEU5dUtu'
prvkey = 'atx:secret:jwk1:6Puzoio5WqXHedmVUj7T8mHAjTAiu9UJrhfrZC96xpLm:DKABn3yMrKzkXrBPuxBsQCpUR8zF14E6P4y5UEU5dUtu:6AMEnawnDFko7J3dnS3RNjQuZ3VaBZs1FoRmdedJcAYi'

#pubkey = 'atx:public:jwk1:3vjt9UAQX6rJm42QQ2X5jRs6372eCDA6VNVyB6NadewJ:9nyJ214RwfBaW8LYA3zPkmCbYrEDqHmwYYxrjUogP2oy'
#prvkey = 'atx:secret:jwk1:3vjt9UAQX6rJm42QQ2X5jRs6372eCDA6VNVyB6NadewJ:9nyJ214RwfBaW8LYA3zPkmCbYrEDqHmwYYxrjUogP2oy:6kDqARDZ8QGPijHmXY4R6LgRHjfhHY53JWNpBvXALi3C'

pub = JWKey.from_custom(pubkey)
prv = JWKey.from_custom(prvkey, private=True)

token = JWToken.make_token(prv, {
    'iss': 'atellix-network',
    'sub': 'catalog-admin',
    'aud': 'atellix-catalog',
})
print(token)

vtoken = JWToken(token)
claims = vtoken.claims(pub)

print(claims)

#webkey = JWKey.generate()
#print(webkey.to_custom(private=True))
#print(webkey.to_custom(private=False))

