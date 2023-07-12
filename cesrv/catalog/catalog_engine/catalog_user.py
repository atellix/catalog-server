import json
import uuid
import pprint
from flask import current_app as app

from note.logging import *
from note.sql import *

CATALOG_BACKENDS = {
    'vendure': True,
}

class CatalogUser():
### Input:
# data
# label
# pubkey
# uri
# uuid
# backends
#  [[backend_name, {config}]]
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
            if 'backends' in userinfo:
                for bk in userinfo['backends']:
                    if bk[0] not in CATALOG_BACKENDS:
                        raise Exception('Invalid backend: {}'.format(bk[0]))
                    cfg = {}
                    if bk == 'vendure':
                        cfg['vendure_url'] = bk[1]['vendure_url']
                    sql_insert('user_backend', {
                        'user_id': sr.sql_id(),
                        'backend_name': bk[0],
                        'config_data': json.dumps(cfg),
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
            if not(isinstance(userinfo['aud'], list)) or userinfo['aud'][0] != 'account' or userinfo['aud'][0] != app.config['KEYCLOAK_CLIENT']:
                raise Exception('Invalid audience: {} for token: {}'.format(userinfo['aud'], auth[7:]))
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
