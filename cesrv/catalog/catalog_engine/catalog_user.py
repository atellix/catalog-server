import json
import uuid
import pprint
from flask import current_app as app

from note.logging import *
from note.sql import *

class CatalogUser():
### Input:
# data
# label
# pubkey
# uri
# uuid
    @staticmethod
    def create_user(userinfo):
        new_user = userinfo['sub']
        nsql.begin()
        try:
            n = sql_now()
            sr = sql_insert('user', {
                'active': True,
                'merchant_data': json.dumps(userinfo.get('data', {})),
                'merchant_label': userinfo.get('label', ''),
                'merchant_pk': userinfo.get('pubkey', None),
                'merchant_uri': userinfo['uri'],
                'ts_created': n,
                'ts_updated': n,
                'uuid': userinfo['uuid'],
            })
            log_warn('User Created: {}'.format(sr.sql_id()))
            nsql.commit()
        except Exception as e:
            nsql.rollback()
            raise e
        return sr

    @staticmethod
    def authorize(token):
        try:
            options = {'verify_signature': True, 'exp': True}
            pem = "-----BEGIN CERTIFICATE----- \n{}\n-----END CERTIFICATE----- ".format(app.config['KEYCLOAK_RS256_PUBLIC']).encode('utf8')
            jk = jwk.JWK.from_pem(pem)
            userinfo = jwt.decode(token, jk, algorithms=['RS256'], options=options, audience='account')
            #log_warn("Userinfo: {}".format(userinfo))
            uuid_bin = uuid.UUID(userinfo['sub']).bytes
            rc = SQLRow('user', uuid=uuid_bin)
            if not(rc.exists()):
                return None
            if not(rc['active']):
                return None
            log_warn('User Authorized: {}'.format(rc.sql_id()))
            return rc
        except Exception as e:
            etxt = "{}: {}\n".format(type(e).__name__, e, ''.join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)[0:-1]))
            log_warn('Login Error: {}'.format(etxt))
            return None
