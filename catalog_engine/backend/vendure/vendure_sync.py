import uuid
import json
import pprint 
import based58
import canonicaljson
from blake3 import blake3
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
        bhash = blake3(cj).digest()
        return based58.b58encode(bhash).decode('utf8')
        
    def generate_listings(self, cat_list):
        gen = {}
        # iterate collections / generate listings
        item = BNode()
        for rc in sorted(cat_list.keys()):
            catv = cat_list[rc][0] # TODO: multiple items in a category
            mrch = catv['merchant']
            dtg = Graph()
            dtg.add( (item, RDF['type'], SCH['OnlineBusiness']) )
            dtg.add( (item, SCH['telephone'], Literal(mrch['telephone'])) )
            dtg.add( (item, SCH['email'], Literal(mrch['email'])) )
            dtg.add( (item, SCH['url'], Literal(mrch['url'])) )
            detail = json.loads(dtg.serialize(format='json-ld', context={'@vocab': 'http://schema.org/'}))
            del detail['@context']
            del detail['@id']
            area = mrch['areaServed']
            # TODO: check if there are parent paths
            locality = [None, None, None]
            locality[0] = area
            label = mrch['name']
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
            pprint.pprint(lst)
            based = self.hash_listing(lst)
            gen[based] = lst
        return gen

    def sync_merchant(self, cat_list):
        print('Sync Merchant')
        # get listings
        catalog_id = 0
        owner = 'G9GUQuEKS6oJsZspUrAJ1aWFqp1SPq5tgCja4wpMueyX'
        q = nsql.table('listing_posted').get(
            table = 'listing_posted lp',
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
            where = {
                'lp.catalog_id': catalog_id,
                'lp.owner': owner,
                'lp.deleted': False,
            },
            debug = True,
        )
        current_listings = {}
        for r in q:
            r['uuid'] = str(uuid.UUID(bytes=r['uuid']))
            lrc = {}
            for k in LISTING_FIELDS:
                lrc[k] = r[k]
            based = self.hash_listing(lrc)
            current_listings[based] = r
        print('Current:')
        pprint.pprint(sorted(current_listings.keys()))
        generated_listings = self.generate_listings(cat_list)
        print('Generated:')
        pprint.pprint(sorted(generated_listings.keys()))
        print('Sync Merchant Done')

