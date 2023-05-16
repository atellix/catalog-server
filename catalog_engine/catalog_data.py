import json
import uuid
import borsh
import pprint
import base64
import based58
import krock32
import typesense
from flask import abort, current_app as app
from borsh import types
from rdflib import URIRef, Namespace
from rdflib.namespace import RDF, RDFS, SKOS
from Crypto.Hash import SHAKE128
from solders.pubkey import Pubkey
from solders.keypair import Keypair

from note.sql import *
from note.rdf_database import rdf_database

SCH = Namespace('http://schema.org/')
GEO = Namespace('http://geo.atellix.net/1.0/')
CAT = Namespace('http://rdf.atellix.com/1.0/schema/catalog/')

class CatalogData():
    def __init__(self):
        self.typesense = typesense.Client({
            'nodes': [{
                'host': app.config['TYPESENSE_HOST'],
                'port': app.config['TYPESENSE_PORT'],
                'protocol': app.config['TYPESENSE_PROTOCOL'],
            }],
            'api_key': app.config['TYPESENSE_API_KEY'],
            'connection_timeout_seconds': 10,
        })
        self.parent_cache = {}

    def uri_hash_bytes(self, uri):
        shake = SHAKE128.new()
        shake.update(uri.encode('utf8'))
        return shake.read(16)

    def store_uri_hash(self, uri):
        uri_hash = self.uri_hash_bytes(uri)
        try:
            sql_insert('uri', {
                'uri_hash': uri_hash,
                'uri': uri,
            })
        except Exception as e:
            pass

    def get_encoded_uri(self, b58_uri):
        bts = based58.b58decode(b58_uri.encode('utf8'))
        if len(bts) != 16:
            return None
        rc = nsql.table('uri').get(
            select = 'uri',
            where = { 'uri_hash': bts },
            result = list,
            limit = 1,
        )
        if len(rc):
            return rc[0][0]
        return None

    def get_resource(self, uri):
        rsrc = self.get_resource_graph(uri)
        return json.loads(rsrc.serialize(format='json-ld'))

    def get_resource_graph(self, uri):
        gdb = rdf_database()
        rsrc = gdb.get_resource(uri)
        return rsrc

    def iterate_parent(self, parent, seen, path = []):
        if parent in seen:
            return path
        seen[parent] = True
        gdb = rdf_database()
        if parent in self.parent_cache:
            item, pt = self.parent_cache[parent]
        else:
            item = {'uri': parent}
            rsrc = gdb.get_resource(parent)
            lbl = None
            for i in [RDFS['label'], SKOS['prefLabel']]:
                lbl = rsrc.value(URIRef(parent), i)
                if lbl:
                    break
            if lbl is not None:
                item['name'] = str(lbl)
            pt = gdb.get(
                select = ['?a'],
                where = [[URIRef(parent), CAT['parentCategory'], '?a']],
            )
            self.parent_cache[parent] = (item, pt.copy())
        path.append(str(item['uri'] + "\t" + item.get('name', '')))
        if len(pt):
            self.iterate_parent(str(pt[0]['a']), seen, path)
        return path

    def get_path(self, parent):
        seen = {}
        path = []
        path = self.iterate_parent(str(parent), seen, path)
        path.reverse()
        return path

    def index_category(self, uri, catalog_index):
        rsrc = self.get_resource_graph(uri)
        ur = URIRef(uri)
        #print(rsrc.serialize(format='turtle'))
        for i in [RDFS['label'], SKOS['prefLabel']]:
            lbl = rsrc.value(ur, i)
            if lbl:
                break
        rec = {
            'uri': uri,
            'name': str(lbl),
            'tree': str(rsrc.value(ur, SKOS['inScheme'])),
            'path': [],
            #'path': 
        }
        par = rsrc.value(ur, CAT['parentCategory'])
        if par:
            rec['parent'] = str(par)
            #rec['path'] = json.dumps(self.get_path(par))
            rec['path'] = self.get_path(par)
        desc = None
        for i in [RDFS['comment'], SKOS['definition']]:
            desc = rsrc.value(ur, i)
            if desc:
                break
        if desc is not None:
            if "\n\n" in desc:
                desc = desc.split("\n\n")[0]
            rec['description'] = desc.strip()
        self.typesense.collections[catalog_index].documents.create(rec)
        #print(rec['name'])
        #print(json.dumps(rec, indent=2))

    def iterate_parent_location(self, parent, seen, path = []):
        if parent in seen:
            return path
        seen[parent] = True
        gdb = rdf_database()
        if parent in self.parent_cache:
            item, pt = self.parent_cache[parent]
        else:
            item = {'uri': parent}
            rsrc = gdb.get_resource(parent)
            lbl = None
            for i in [RDFS['label'], SCH['name']]:
                lbl = rsrc.value(URIRef(parent), i)
                #print(parent, i, lbl)
                if lbl:
                    break
            if lbl is not None:
                item['name'] = str(lbl)
            pt = gdb.get(
                select = ['?a'],
                where = [[URIRef(parent), SCH['geoWithin'], '?a']],
            )
            self.parent_cache[parent] = (item, pt.copy())
        path.append(str(item['uri'] + "\t" + item.get('name', '')))
        if len(pt):
            self.iterate_parent_location(str(pt[0]['a']), seen, path)
        return path

    def get_location_path(self, parent):
        seen = {}
        path = []
        path = self.iterate_parent_location(str(parent), seen, path)
        path.reverse()
        return path

    def index_location(self, uri):
        rsrc = self.get_resource_graph(uri)
        ur = URIRef(uri)
        geotype = None
        for ty in [GEO['Country'], GEO['Region'], GEO['City'], GEO['PostalCode']]:
            if (ur, RDF['type'], ty) in rsrc:
                geotype = str(ty).split('/')[-1]
                break
        for i in [RDFS['label'], SCH['name']]:
            lbl = rsrc.value(ur, i)
            if lbl:
                break
        if geotype is not None:
            cc = str(rsrc.value(ur, GEO['countryCode']))
            rec = {
                'uri': uri,
                'name': str(lbl),
                'geoname': str(rsrc.value(ur, GEO['geoname'])),
                'geoname_id': str(rsrc.value(ur, GEO['geonameID'])),
                'type': str(geotype),
                'country_code': cc,
                'path': [],
            }
            if geotype == 'Region':
                regc = str(rsrc.value(ur, GEO['regionCode']))
                if cc == 'US':
                    rec['region_code'] = regc.split('-')[-1]
            elif geotype == 'City':
                regc = str(rsrc.value(ur, GEO['regionCode']))
                if cc == 'US':
                    rec['region_code'] = regc.split('-')[-1]
            elif geotype == 'PostalCode':
                regc = str(rsrc.value(ur, GEO['regionCode']))
                if cc == 'US':
                    rec['region_code'] = regc.split('-')[-1]
                rec['postal_code'] = str(rsrc.value(ur, GEO['postalCode']))
            if geotype == 'PostalCode':
                lat = str(rsrc.value(ur, URIRef('http://www.w3.org/2003/01/geo/wgs84_pos#lat')))
                lon = str(rsrc.value(ur, URIRef('http://www.w3.org/2003/01/geo/wgs84_pos#long')))
                rec['location'] = [float(lat), float(lon)]
            else:
                gnrc = self.get_resource_graph(rec['geoname'])
                gn = URIRef(rec['geoname'])
                lat = str(gnrc.value(gn, URIRef('http://www.w3.org/2003/01/geo/wgs84_pos#lat')))
                lon = str(gnrc.value(gn, URIRef('http://www.w3.org/2003/01/geo/wgs84_pos#long')))
                rec['location'] = [float(lat), float(lon)]
            within = rsrc.value(ur, SCH['geoWithin'])
            if within is not None:
                rec['parent'] = str(within)
                rec['path'] = self.get_location_path(within)
            self.typesense.collections['geo_location'].documents.create(rec)
            #print(rec)

