import os
import boto3
import based58
import secrets
import requests
from blake3 import blake3
from urllib.parse import urlparse
from flask import current_app as app

from note.logging import *
from note.sql import *

class MediaCache(object):
    def __init__(self, user_id):
        self.user_id = user_id
        self.s3 = boto3.resource('s3',
            endpoint_url = 'https://s3.{}.amazonaws.com'.format(app.config['MEDIA_AWS_REGION']),
            aws_access_key_id = app.config['MEDIA_AWS_ACCESS_KEY_ID'],
            aws_secret_access_key = app.config['MEDIA_AWS_SECRET_ACCESS_KEY'],
        )

    def is_cached(self, media_url):
        rc = sql_row('user_media', user_id=self.user_id, media_url=media_url)
        return rc.exists()

    def public_url(self, media_rc):
        parsed = urlparse(media_rc['media_url'])
        filename = os.path.basename(parsed.path)
        public_key = self.make_base58(media_rc['public_key'])
        url = 'https://{}/api/catalog/media/{}/{}'.format(app.config['NGINX_HOST'], public_key, filename)
        return url

    def new_public_key(self):
        for i in range(10):
            token = secrets.token_bytes(10)
            rc = sql_row('user_media', public_key=token)
            if not(rc.exists()):
                return token
        raise Exception('Duplicate public key after 10 tries')

    def import_url(self, media_url):
        r = requests.get(media_url)
        if r.status_code != 200:
            return None
        mime_type = r.headers['content-type']
        remote_cksum = self.make_cksum(r.content)
        cloud_path = app.config['MEDIA_CLOUD_PREFIX'] + '{}/{}'.format(self.user_id, remote_cksum)
        rc = sql_row('user_media', user_id=self.user_id, media_url=media_url)
        if rc.exists():
            if remote_cksum == rc['media_cksum']:
                # Same data exists in cache
                return self.public_url(rc)
            # Update cached data
            self.s3.Bucket(app.config['MEDIA_AWS_BUCKET']).put_object(
                Key = cloud_path,
                Body = r.content,
            )
            rc.update({
                'cloud_path': cloud_path,
                'mime_type': mime_type,
                'ts_updated': sql_now(),
            })
        else:
            self.s3.Bucket(app.config['MEDIA_AWS_BUCKET']).put_object(
                Key = cloud_path,
                Body = r.content,
            )
            n = sql_now()
            rc = sql_insert('user_media', {
                'user_id': self.user_id,
                'public_key': self.new_public_key(),
                'media_url': media_url,
                'media_cksum': remote_cksum,
                'cloud_path': cloud_path,
                'mime_type': mime_type,
                'ts_created': n,
                'ts_updated': n,
                'ts_deleted': None,
                'deleted': False,
            })
        return self.public_url(rc)

    def make_cksum(self, data):
        bhash = blake3(data).digest()
        return based58.b58encode(bhash).decode('utf8')

    def make_base58(self, data):
        return based58.b58encode(data).decode('utf8')

    def get_cksum(self, media_url):
        rc = sql_row('user_media', user_id=self.user_id, media_url=media_url)
        if not(rc.exists()):
            return None
        return rc['cksum']

    def get_data_by_key(self, key_base58):
        public_key = based58.b58decode(key_base58.encode('utf8'))
        rc = sql_row('user_media', public_key=public_key)
        if not(rc.exists()):
            return None, None
        #log_warn('Cloud path: {}'.format(rc['cloud_path']))
        response = self.s3.Object(
            bucket_name = app.config['MEDIA_AWS_BUCKET'],
            key = rc['cloud_path'],
        ).get()
        return response['Body'].read(), rc['mime_type']

