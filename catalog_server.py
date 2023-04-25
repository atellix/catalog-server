#!/usr/bin/env python3

import os
import json
import uuid
from rdflib import Graph, URIRef
from flask import Flask, request, jsonify, abort
from flask_cors import CORS, cross_origin

os.environ['DB_DATABASE'] = 'atellix_catalog'
os.environ['DB_USER'] = 'catalog'
os.environ['DB_HOST'] = 'atx2.atellix.net'
os.environ['DB_PORT'] = '3306'
os.environ['CATALOG_PROGRAM'] = '7YX5ettF4ZZBEjkBbDTP98rFPz6UqrsGdT8wtp5UwtLd'
os.environ['CATALOG_SIGNER'] = 'dct82560hw3ap63hpq28m41tetv076tytsgh6fny79y9d5kcxrq9qwnpxt5xewxsc45wzx77qcpsx74ptv18ry92j825s4r81gc3pt0'
os.environ['CATALOG_FEE_MINT'] = 'USDVXgXZcQWycX4PAu2CZbGaSG1Ft5rNjo4ARpoqw7w'
os.environ['CATALOG_FEE_ACCOUNT'] = '6sGyBbpzTBaJ5U1kxmdhA9wpfxjcVQ5mymUJcWFCqwSt'
os.environ['DB_PORT'] = '3306'
import config

from note.sql import *
from note.database import db, checkout_listener

from catalog_engine import CatalogEngine
from catalog_engine.backend.vendure_backend import VendureBackend

CATALOGS = {
    'commerce': 0,
}

app = Flask(__name__)
app.config.from_object('config.{}'.format(config.flask_config))
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
db.init_app(app)
print(app.config['SQLALCHEMY_DATABASE_URI'])
SQLDatabase('default', db.get_engine(app=app), dialect='mysql')

@app.route("/api/catalog/sign_listing", methods=['POST'])
def sign_listing():
    inp = request.json
    if not isinstance(inp, dict):
        abort(500)
    ce = CatalogEngine()
    res = {}
    print(app.config)
    cfg = {
        'catalog_program': app.config['CATALOG_PROGRAM'],
        'signer_secret': app.config['CATALOG_SIGNER'],
        'fee_mint': app.config['CATALOG_FEE_MINT'],
        'fee_account': app.config['CATALOG_FEE_ACCOUNT'],
        'fee_tokens': 0,
    }
    res.update(ce.sign_listing(cfg, inp))
    res['result'] = 'ok'
    #print(res)
    return jsonify(res)

@app.route("/api/catalog/listing/<listing_uuid>", methods=['POST', 'GET'])
@cross_origin()
def catalog_listing(listing_uuid):
    res = {}
    listing_uuid_bytes = uuid.UUID(listing_uuid).bytes
    if request.method == 'POST':
        inp = request.json
        user_uuid_bytes = uuid.UUID(inp['user']).bytes
        record_uuid_bytes = uuid.UUID(inp['record']).bytes
        u = sql_row('user', uuid=user_uuid_bytes)
        now = sql_now()
        if not(u.exists()):
            u = sql_insert('user', {
                'uuid': user_uuid_bytes,
                'ts_created': now,
                'ts_updated': now,
            })
        rec = sql_row('record', uuid=record_uuid_bytes)
        if not(rec.exists()):
            if inp.get('data', False):
                rec = sql_insert('record', {
                    'user_id': u.sql_id(),
                    'uuid': record_uuid_bytes,
                    'data': json.dumps(inp['data']),
                    'ts_created': now,
                    'ts_updated': now,
                })
            else:
                abort(404)
        elif inp.get('data', False):
            rec.update({
                'data': json.dumps(inp['data']),
                'ts_updated': now,
            })
        r = sql_row('listing', uuid=listing_uuid_bytes)
        if r.exists():
            if inp.get('remove', False):
                r.delete()
            else:
                r.update({
                    'record_id': rec.sql_id(),
                    'ts_updated': now,
                })
        else:
            sql_insert('listing', {
                'uuid': listing_uuid_bytes,
                'catalog': inp['catalog'],
                'record_id': rec.sql_id(),
                'user_id': u.sql_id(),
                'ts_created': now,
                'ts_updated': now,
                'update_count': 0,
                'listing_data': '{}',
            })
        res['result'] = 'ok'
        return jsonify(res)
    # GET method
    lst = sql_row('listing', uuid=listing_uuid_bytes)
    if not(lst.exists()):
        abort(404)
    rec = sql_row('record', id=lst['record_id'])
    if not(rec.exists()):
        abort(404)
    res['data'] = json.loads(rec['data'])
    res['record_uuid'] = str(uuid.UUID(bytes=rec['uuid']))
    res['result'] = 'ok'
    return jsonify(res)

@app.route("/api/catalog/record/<user_uuid>/<record_uuid>", methods=['POST', 'GET'])
@cross_origin()
def catalog_record(user_uuid, record_uuid):
    res = {}
    user_uuid_bytes = uuid.UUID(user_uuid).bytes
    record_uuid_bytes = uuid.UUID(record_uuid).bytes
    u = sql_row('user', uuid=user_uuid_bytes)
    if request.method == 'POST':
        inp = request.json
        now = sql_now()
        if not(u.exists()):
            u = sql_insert('user', {
                'uuid': user_uuid_bytes,
                'ts_created': now,
                'ts_updated': now,
            })
        r = sql_row('record', user_id=u.sql_id(), uuid=record_uuid_bytes)
        if r.exists():
            if inp.get('remove', False):
                r.delete()
            else:
                r.update({
                    'data': json.dumps(inp['data']),
                    'ts_updated': now,
                })
        else:
            r = sql_insert('record', {
                'user_id': u.sql_id(),
                'uuid': record_uuid_bytes,
                'data': json.dumps(inp['data']),
                'ts_created': now,
                'ts_updated': now,
            })
        res['result'] = 'ok'
        return jsonify(res)
    # GET method
    if not(u.exists()):
        abort(404)
    r = sql_row('record', user_id=u.sql_id(), uuid=record_uuid_bytes)
    if not(r.exists()):
        abort(404)
    res['data'] = json.loads(r['data'])
    res['result'] = 'ok'
    return jsonify(res)

# Load a product from a merchant
@app.route("/api/catalog/product/<merchant_id>/<product_id>", methods=['POST', 'GET'])
@cross_origin()
def catalog_product(merchant_id, product_id):
    if request.method == 'POST':
        inp = request.json
        if not isinstance(inp, dict):
            abort(500)
    else:
        inp = {}
    res = {}
    # TODO: find merchant
    gr = Graph()
    with open('merchant.rdf') as f:
        gr.parse(data=f.read(), format='xml')
    vurl = 'http://173.234.24.74:3000/shop-api'
    vb = VendureBackend(URIRef('https://savvyco.com/'), vurl)
    item_uuid = vb.build_product(gr, product_id)
    print(gr.serialize(format='turtle'))
    jsld = gr.serialize(format='json-ld')
    print(item_uuid)
    res['product'] = json.loads(jsld)
    res['product_uuid'] = item_uuid
    res['result'] = 'ok'
    return jsonify(res)

