import uuid
import json
import pprint 
import based58
import canonicaljson
from blake3 import blake3
from Crypto.Hash import SHAKE128
from rdflib import Graph, Literal, URIRef, Namespace, BNode
from rdflib.namespace import RDF, SKOS, RDFS, XSD, OWL, DC, DCTERMS

from note.sql import *

SCH = Namespace('http://schema.org/')

LISTING_FIELDS = ['category', 'filter_by_1', 'filter_by_2', 'filter_by_3', 'label', 'latitude', 'longitude', 'detail', 'attributes']

class VendureSync(object):
    def __init__(self, vendure_client):
        self.vendure_client = vendure_client

    def hash_listing(self, listing):
        cj = canonicaljson.encode_canonical_json(listing)
        #print(cj)
        bhash = blake3(cj).digest()
        based = based58.b58encode(bhash).decode('utf8')
        #print(based)
        return based

    def uri_hash_bytes(self, uri):
        shake = SHAKE128.new()
        shake.update(uri.encode('utf8'))
        return shake.read(16)

    def generate_listings(self, backend_id, cat_list):
        gen = {}
        # iterate collections / generate listings
        item = BNode()
        for rc in sorted(cat_list.keys()):
            catv = cat_list[rc][0] # TODO: multiple items in a category
            mrch = catv['merchant']
            dtg = Graph()
            dtg.add( (item, RDF['type'], SCH['OnlineBusiness']) )
            if 'name' in mrch:
                dtg.add( (item, SCH['name'], Literal(mrch['name'])) )
            if 'telephone' in mrch:
                dtg.add( (item, SCH['telephone'], Literal(mrch['telephone'])) )
            if 'email' in mrch:
                dtg.add( (item, SCH['email'], Literal(mrch['email'])) )
            if 'url' in mrch:
                dtg.add( (item, SCH['url'], Literal(mrch['url'])) )
            detail = json.loads(dtg.serialize(format='json-ld', context={'@vocab': 'http://schema.org/'}))
            del detail['@context']
            del detail['@id']
            # TODO: check if there are parent paths
            locality = [None, None, None]
            if 'areaServed' in mrch:
                area = mrch['areaServed']
                locality[0] = area
            label = catv['name']
            lon = None
            lat = None
            # TODO: dynamic attributes
            attributes = {'LocalDelivery': True}
            lst = { 
                'category': rc,
                'filter_by_1': locality[0],
                'filter_by_2': locality[1],
                'filter_by_3': locality[2],
                'label': label,
                'latitude': lat,
                'longitude': lon,
                'detail': detail,
                'attributes': attributes,
            }
            #pprint.pprint(lst)
            based = self.hash_listing(lst)
            # Store attributes as a list
            lst['attributes'] = sorted(list(attributes.keys()))
            lst['data'] = []
            for data in cat_list[rc]:
                lst['data'].append({
                    'name': data['name'],
                    'collection': data['collection'],
                })
            gen[based] = lst
        return gen

    def get_diff(self, source_data, target_data):
        """
        Calculates the difference between source_data and target_data.
        Returns a tuple of added and removed items.
        """
        added_items = []
        removed_items = []

        # Find added items
        for item in source_data:
            if item not in target_data:
                added_items.append(item)

        # Find removed items
        for item in target_data:
            if item not in source_data:
                removed_items.append(item)

        return added_items, removed_items

    def sync_listings(self, user_rc, catalog_id, backend_id, cat_list):
        # get listings
        user_id = user_rc.sql_id()
        owner = user_rc['merchant_pk']
        q = nsql.table('listing_posted').get(
            table = ['listing_posted lp', 'listing_backend b'],
            select = [
                'lp.id',
                'lp.uuid',
                'lp.listing_idx',
                'lp.listing_account',
                '(select uri.uri from uri where uri.uri_hash=lp.category_hash) as category',
                '(select uri.uri from uri where uri.uri_hash=lp.filter_by_1) as filter_by_1',
                '(select uri.uri from uri where uri.uri_hash=lp.filter_by_2) as filter_by_2',
                '(select uri.uri from uri where uri.uri_hash=lp.filter_by_3) as filter_by_3',
                'lp.label',
                'lp.latitude',
                'lp.longitude',
                'lp.detail',
                'lp.attributes',
            ],
            join = ['lp.uuid=b.uuid'],
            where = {
                'lp.catalog_id': catalog_id,
                'lp.owner': owner,
                'lp.deleted': False,
                'b.backend_id': backend_id,
            },
        )
        #print('Current:')
        current_listings = {}
        for r in q:
            r['uuid'] = str(uuid.UUID(bytes=r['uuid']))
            r['detail'] = json.loads(str(r['detail']))
            r['attributes'] = json.loads(str(r['attributes']))
            lrc = {}
            for k in LISTING_FIELDS:
                lrc[k] = r[k]
            based = self.hash_listing(lrc)
            current_listings[based] = r
        #pprint.pprint(sorted(current_listings.keys()))
        #print('Generated:')
        generated_listings = self.generate_listings(backend_id, cat_list)
        #pprint.pprint(sorted(generated_listings.keys()))
        lst_add, lst_remove = self.get_diff(generated_listings, current_listings)
        #print('Add')
        #print(lst_add)
        #print('Remove')
        #print(lst_remove)
        listing_add = []
        listing_remove = []
        for r in lst_add:
            gr = generated_listings[r]
            gr_data = gr['data']
            del gr['data']
            cat_hash = self.uri_hash_bytes(gr['category'])
            spec = sql_row('listing_spec',
                catalog_id = catalog_id,
                backend_id = backend_id,
                category_hash = cat_hash,
                owner = owner,
            )
            if spec.exists():
                spec.update({
                    'listing_data': json.dumps(gr_data),
                    'ts_updated': sql_now(),
                })
            else:
                n = sql_now()
                sql_insert('listing_spec', {
                    'catalog_id': catalog_id,
                    'user_id': user_id,
                    'backend_id': backend_id,
                    'category_hash': cat_hash,
                    'listing_data': json.dumps(gr_data),
                    'owner': owner,
                    'ts_created': n,
                    'ts_updated': n,
                })
            listing_add.append(gr)
        for r in lst_remove:
            listing_remove.append(current_listings[r]['listing_account'])
        return {
            'listing_add': listing_add,
            'listing_remove': listing_remove,
        }

