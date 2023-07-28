import uuid
import json
import requests
import canonicaljson
from blake3 import blake3
from rdflib import Graph, Literal, URIRef, Namespace, BNode
from rdflib.namespace import RDF, SKOS, RDFS, XSD, OWL, DC, DCTERMS
from flask import current_app as app

from note.sql import * 
from note.logging import *
from catalog_engine.rdf_data import DataCoder
from catalog_engine.backend.vendure_backend import VendureBackend
from .sync_data import DataSync

class SyncEntries(DataSync):
    def __init__(self, backend, listing, listing_params):
        self.backend = backend
        self.listing = listing
        self.listing_params = listing_params
        self.obj_schema = app.config['CATALOG_SCHEMA']
        self.update = True
        self.src_data = {}
        self.dst_data = {}

    def load(self):
        bk = self.backend['backend_name']
        bkid = self.backend.sql_id()
        log_warn('Sync: {}'.format(self.backend.data()))
        if bk == 'vendure':
            gr = Graph()
            backend_data = json.loads(self.backend['config_data'])
            vb = VendureBackend(bkid, gr, URIRef(self.listing['merchant_uri']), backend_data['vendure_url'])
            seen = {}
            for rc in self.listing_params:
                coll = vb.get_collection(rc['collection']['slug'])
                #log_warn('Collection: {} {}'.format(rc, coll))
                for prod in coll['products']:
                    #log_warn(prod['productId'])
                    pgr = Graph()
                    slug = None
                    data_summary = None
                    indexfield = {}
                    current = sql_row('entry', backend_id=bkid, external_id=prod['productId'])
                    if current.exists():
                        record_uuid = str(uuid.UUID(bytes=current['uuid']))
                    else:
                        record_uuid = str(uuid.uuid4())
                    obj_list = vb.get_product_spec(prod['productId'])
                    for idx in range(len(obj_list)):
                        obj = obj_list[idx]
                        if idx == 0:
                            obj['uuid'] = record_uuid
                            if 'alternateName' in obj:
                                slug = obj['alternateName'].lower()
                            elif 'name' in obj:
                                slug = self.convert_to_slug(obj['name'])
                            summ = vb.summarize_product_spec(obj)
                            if 'name' in summ:
                                indexfield['name'] = summ['name']
                            if 'offers' in summ:
                                if 'price' in summ['offers'][0]:
                                    indexfield['price'] = summ['offers'][0]['price']
                            # TODO: index brand (to string)
                            sgr = Graph()
                            summ_coder = DataCoder(self.obj_schema, sgr, summ['id'])
                            summ_coder.encode_rdf(summ)
                            data_summary = self.json_hash(json.loads(sgr.serialize(format='json-ld')), digest=False)
                        coder = DataCoder(self.obj_schema, pgr, obj['id'])
                        coder.encode_rdf(obj)
                    jsld = json.loads(pgr.serialize(format='json-ld'))
                    data, data_hash = self.json_hash(jsld)
                    src_entry = {
                        'external_uri': obj_list[0]['id'],
                        'uuid': record_uuid,
                        'slug': slug,
                        #'data': data,
                        'data_hash': data_hash,
                        #'data_summary': data_summary, 
                        'entry_name': indexfield.get('name', None),
                        'entry_brand': indexfield.get('brand', None),
                        'entry_price': indexfield.get('price', None),
                    }
                    log_warn(src_entry)

    def src_items(self):
        return self.src_data.keys()

    def src_has(self, item):
        res = item in self.src_data
        return res

    def dst_items(self):
        return self.dst_data.keys()

    def dst_has(self, item):
        res = item in self.dst_data
        return res

    def dst_add(self, item):
        pass

    def dst_delete(self, item):
        pass

    def dst_eq(self, new_item):
        pass

    def dst_update(self, orig_item, new_item):
        pass

    def json_hash(self, data, digest=True):
        enc = canonicaljson.encode_canonical_json(data)
        if digest:
            hs = blake3()
            hs.update(enc)
            return enc.decode('utf8'), hs.digest() 
        else:
            return enc.decode('utf8')

    def convert_to_slug(self, label):
        # Convert to lower case
        slug = label.lower()
        # Remove extra characters
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        # Replace spaces with '-'
        slug = re.sub(r'\s+', '-', slug)
        return slug

