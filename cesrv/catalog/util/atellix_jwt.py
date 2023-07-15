import re
import json
import pytz
import base58
import base64
import secrets
from dateutil.parser import isoparse
from datetime import datetime, timedelta
from jwcrypto import jwk, jwt, jws

from note.exceptions import AccessDenied

__all__ = [
    'JWKey',
    'JWToken',
]

class JWKey(object):
    def __init__(self, jwk):
        self.jwk = jwk

    @staticmethod
    def generate():
        return JWKey(jwk.JWK.generate(kty='EC', crv='P-256'))

    @staticmethod
    def from_custom(inp, private=False):
        if private:
            if not(inp.startswith('atx:secret:jwk1:')):
                raise Exception('Invalid key prefix')
            parts = inp[len('atx:secret:jwk1:'):].split(':')
            parts[0] = base58.b58decode(parts[0])
            parts[1] = base58.b58decode(parts[1])
            parts[2] = base58.b58decode(parts[2])
            parts[0] = re.sub('\=+$', '', base64.urlsafe_b64encode(parts[0]).decode('utf8'))
            parts[1] = re.sub('\=+$', '', base64.urlsafe_b64encode(parts[1]).decode('utf8'))
            parts[2] = re.sub('\=+$', '', base64.urlsafe_b64encode(parts[2]).decode('utf8'))
            skey = { 'kty': 'EC', 'crv': 'P-256', 'x': parts[0], 'y': parts[1], 'd': parts[2] }
        else:
            if not(inp.startswith('atx:public:jwk1:')):
                raise Exception('Invalid key prefix')
            parts = inp[len('atx:public:jwk1:'):].split(':')
            parts[0] = base58.b58decode(parts[0])
            parts[1] = base58.b58decode(parts[1])
            parts[0] = re.sub('\=+$', '', base64.urlsafe_b64encode(parts[0]).decode('utf8'))
            parts[1] = re.sub('\=+$', '', base64.urlsafe_b64encode(parts[1]).decode('utf8'))
            skey = { 'kty': 'EC', 'crv': 'P-256', 'x': parts[0], 'y': parts[1] }
        return JWKey(jwk.JWK.from_json(json.dumps(skey)))

    @staticmethod
    def from_pem(inp):
        return JWKey(jwk.JWK.from_pem(inp))

    def thumbprint(self):
        return self.jwk.thumbprint()

    def to_pem(self):
        return self.jwk.export_to_pem().decode('utf8')

    def to_url(self):
        return 'jwt://pubkey/' + self.thumbprint()

    def to_custom(self, private=False):
        if private:
            k = json.loads(self.jwk.export_private())
            x = k['x'] + ('=' * (-len(k['x']) % 4))
            y = k['y'] + ('=' * (-len(k['y']) % 4))
            d = k['d'] + ('=' * (-len(k['d']) % 4))
            x = base64.urlsafe_b64decode(x)
            y = base64.urlsafe_b64decode(y)
            d = base64.urlsafe_b64decode(d)
            x = base58.b58encode(x).decode('utf8')
            y = base58.b58encode(y).decode('utf8')
            d = base58.b58encode(d).decode('utf8')
            return 'atx:secret:jwk1:{}:{}:{}'.format(x, y, d)
        else:
            k = json.loads(self.jwk.export_public())
            x = k['x'] + ('=' * (-len(k['x']) % 4))
            y = k['y'] + ('=' * (-len(k['y']) % 4))
            x = base64.urlsafe_b64decode(x)
            y = base64.urlsafe_b64decode(y)
            x = base58.b58encode(x).decode('utf8')
            y = base58.b58encode(y).decode('utf8')
            return 'atx:public:jwk1:{}:{}'.format(x, y)

class JWToken(object):
    def __init__(self, jwt_input):
        jws1 = jwt.JWS()
        self.jwt = jwt_input
        self.jws = jws1
        jws1.deserialize(jwt_input)
        if jws1.jose_header['alg'] != 'ES256':
            raise AccessDenied('Invalid JWS algorithm: ' + jws1.jose_header['alg'])
        expires_dt = isoparse(jws1.jose_header['exp'])
        if expires_dt <= datetime.utcnow().replace(tzinfo=pytz.UTC):
            raise AccessDenied('JWT expired at: {}'.format(expires_dt.strftime("%FT%TZ")))
        self.key_id = jws1.jose_header['kid']
        self.verified_sig = False
        self.verified_nonce = False

#    @staticmethod
#    def verify_nonce(nonce):
#        nd = base58.b58decode(nonce)
#        if len(nd) != 32:
#            raise Exception('Invalid nonce length: {} != 32'.format(len(nd)))
#        # TODO: Exception handing
#        sql_insert('note_nonce', {'nonce': nd})

    def verify(self, verify_key):
        try:
            self.jws.verify(verify_key.jwk, alg='ES256')
        except jws.InvalidJWSSignature as e:
            raise AccessDenied('Invalid JWS signature for key: ' + verify_key.thumbprint())
        self.verified_sig = True

    def claims(self, verify_key):
        if not(self.verified_sig):
            self.verify(verify_key)
        data = jwt.JWT(key=verify_key.jwk, jwt=self.jwt)
        rec = json.loads(data.claims)
#        if not(self.verified_nonce):
#            JWToken.verify_nonce(rec['nonce'])
#            self.verified_nonce = True
        return rec

    @staticmethod
    def make_token(keyobj, claims, expires=None):
        if expires is None:
            expires_dt = datetime.utcnow() + timedelta(hours=1)
            expires = expires_dt.strftime("%FT%TZ")
        nonce = base58.b58encode(secrets.token_bytes(32)).decode('utf8')
        data = claims.copy()
        data['nonce'] = nonce
        token = jwt.JWT(
            header = {"alg": "ES256", "kid": keyobj.jwk.thumbprint(), "exp": expires},
            claims = data,
        )
        token.make_signed_token(keyobj.jwk)
        return token.serialize()

