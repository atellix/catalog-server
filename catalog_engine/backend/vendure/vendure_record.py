#!/usr/bin/env python3

import uuid
import pprint
from decimal import Decimal, ROUND_DOWN
from rdflib import plugin, Graph, Literal, URIRef, Namespace, BNode
from rdflib.namespace import RDF, SKOS, RDFS, XSD, OWL, DC, DCTERMS

SCH = Namespace('http://schema.org/')
CAT = Namespace('http://example.com/product#')
ATX = Namespace('http://rdf.atellix.com/schema/catalog/')

class VendureRecordBuilder(object):
    def __init__(self, vendure_client, gr):
        self.vendure_client = vendure_client
        self.graph = gr
        self.lists = {}
        self.opts_ids = {}
        self.opts_uri = {}
        self.opts_code = {}
        self.opts_group_ids = {}
        dts = CAT['terms.products']
        gr.add( (dts, RDF['type'], SCH['DefinedTermSet']) )
        gr.add( (dts, SCH['identifier'], Literal('slug')) )
        self.terms_product_slug = dts

    def build_catalog(self):
        gr = self.graph
        catsch = CAT['catalog']
        gr.add( (catsch, RDF['type'], SKOS['ConceptScheme']) )
        topc = CAT['catalog.root']
        gr.add( (topc, RDF['type'], SKOS['Concept']) )
        gr.add( (topc, SKOS['topConceptOf'], catsch) )
        gr.add( (catsch, SKOS['hasTopConcept'], topc) )
        vcl = self.vendure_client
        cts = vcl.get_category()
        cat_ids = {}
        for category in cts['collections']['items']:
            slug = category['slug']
            parent = category['parent']
            #print('{} -> {}: {}'.format(parent['id'], category['id'], slug))
            cat_ids[category['id']] = {
                'id': category['id'],
                'name': category['name'],
                'slug': category['slug'],
                'parent': category['parent']['id'],
                'urls': category['customFields']['atellixUrl'],
            }
        for cid in sorted(cat_ids.keys()):
            cat_data = cat_ids[cid]
            catrc = CAT[f"catalog.{cid}"]
            cat_data['uri'] = catrc
        for cid in sorted(cat_ids.keys()):
            cat_data = cat_ids[cid]
            catrc = cat_data['uri']
            gr.add( (catrc, RDF['type'], SKOS['Concept']) )
            gr.add( (catrc, RDF['type'], SCH['ProductCollection']) )
            gr.add( (catrc, SCH['identifier'], Literal(cat_data['id'])) )
            gr.add( (catrc, SCH['name'], Literal(cat_data['name'])) )
            gr.add( (catrc, SCH['alternateName'], Literal(cat_data['slug'])) )
            for url in cat_data['urls']:
                gr.add( (catrc, SCH['additionalType'], URIRef(url)) )
            if int(cat_data['parent']) == 1:
                gr.add( (catrc, SKOS['broader'], topc) )
                gr.add( (topc, SKOS['narrower'], catrc) )
            else:
                par = cat_ids[cat_data['parent']]['uri']
                gr.add( (catrc, SKOS['broader'], par) )
                gr.add( (par, SKOS['narrower'], catrc) )
        return catsch

    def get_catalog_category(self, collection_slug):
        vcl = self.vendure_client
        citems = vcl.get_facet(collectionSlug=collection_slug)
        prod_ids = []
        for product in citems['search']['items']:
            prod_ids.append(product['productId'])
        return prod_ids

    def build_list(self, gr):
        itemlist = CAT['list.' + str(uuid.uuid4())]
        self.lists[str(itemlist)] = 0
        gr.add( (itemlist, RDF['type'], SCH['ItemList']) )
        return itemlist

    def add_to_list(self, gr, itemlist, val):
        ct = self.lists[str(itemlist)]
        item = CAT['item.' + str(uuid.uuid4())]
        gr.add( (itemlist, SCH['itemListElement'], item) )
        gr.add( (item, RDF['type'], SCH['ListItem']) )
        gr.add( (item, SCH['position'], Literal(ct)) )
        gr.add( (item, SCH['item'], val) )
        self.lists[str(itemlist)] = ct + 1
        return item

    def build_product(self, product_id, merchant_uri, link_collections=False):
        vcl = self.vendure_client
        detail = vcl.get_product(product_id)
        #print(detail)
        gr = self.graph
        product_key = detail['product']['id']
        item = CAT[f"product.{product_key}"]
        item_uuid = str(uuid.uuid4())
        gr.add( (item, ATX['Object.uuid'], URIRef(f'urn:uuid:{item_uuid}')) )
        var_ct = len(detail['product']['variants'])
        if var_ct == 1:
            var_data = detail['product']['variants'][0]
            gr.add( (item, RDF['type'], SCH['Product']) )
            gr.add( (item, SCH['name'], Literal(detail['product']['name'])) )
            gr.add( (item, SCH['productID'], Literal(detail['product']['id'])) )
            gr.add( (item, SCH['sku'], Literal(var_data['sku'])) )
            # Offer
            offer = CAT[f"product.{product_key}.offer"]
            gr.add( (item, SCH['offers'], offer) )
            gr.add( (offer, RDF['type'], SCH['Offer']) )
            gr.add( (offer, SCH['offeredBy'], merchant_uri) )
            # Base Price
            price = Decimal(var_data['price']) / Decimal(100)
            gr.add( (offer, SCH['price'], Literal(price.quantize(Decimal('.01'), rounding=ROUND_DOWN))) )
            gr.add( (offer, SCH['priceCurrency'], Literal(var_data['currencyCode'])) )
        else:
            gr.add( (item, RDF['type'], SCH['ProductGroup']) )
            gr.add( (item, SCH['name'], Literal(detail['product']['name'])) )
            gr.add( (item, SCH['identifier'], Literal(detail['product']['id'])) )
            main_offer = CAT[f"product_group.{product_key}.offer"]
            gr.add( (main_offer, RDF['type'], SCH['Offer']) )
            gr.add( (item, SCH['offers'], main_offer) )
            gr.add( (main_offer, SCH['offeredBy'], merchant_uri) )
            variant_list = self.build_list(gr)
            gr.add( (item, SCH['hasVariant'], variant_list) )
            for var_data in detail['product']['variants']:
                variant_key = var_data['id']
                model = CAT[f"product.{product_key}.{variant_key}"]
                list_item = self.add_to_list(gr, variant_list, model)
                gr.add( (model, RDF['type'], SCH['Product']) )
                gr.add( (model, SCH['name'], Literal(var_data['name'])) )
                gr.add( (model, SCH['identifier'], Literal(var_data['id'])) )
                gr.add( (model, SCH['sku'], Literal(var_data['sku'])) )
                # Options groups
                for opts_grp in detail['product']['optionGroups']:
                    if opts_grp['id'] in self.opts_group_ids:
                        opts_set = self.opts_group_ids[opts_grp['id']]
                    else:
                        opts_set = CAT[f"terms.{opts_grp['code']}"]
                        self.opts_group_ids[opts_grp['id']] = opts_set
                        gr.add( (opts_set, RDF['type'], SCH['DefinedTermSet']) )
                        gr.add( (opts_set, SCH['name'], Literal(opts_grp['name'])) )
                        gr.add( (opts_set, SCH['identifier'], Literal(opts_grp['id'])) )
                        gr.add( (opts_set, SCH['alternateName'], Literal(opts_grp['code'])) )
                        for opts_item in opts_grp['options']:
                            opts_val = CAT[f"terms.{opts_grp['code']}.{opts_item['code']}"]
                            gr.add( (opts_val, RDF['type'], SCH['DefinedTerm']) )
                            gr.add( (opts_val, SCH['inDefinedTermSet'], opts_set) )
                            gr.add( (opts_set, SCH['hasDefinedTerm'], opts_val) )
                            gr.add( (opts_val, SCH['name'], Literal(opts_item['name'])) )
                            gr.add( (opts_val, SCH['identifier'], Literal(opts_item['id'])) )
                            gr.add( (opts_val, SCH['alternateName'], Literal(opts_item['code'])) )
                            self.opts_ids[opts_item['id']] = opts_val
                            self.opts_uri[opts_item['id']] = opts_set
                            self.opts_code[opts_item['id']] = opts_grp['code']
                for i in range(len(var_data['options'])):
                    var_opt = var_data['options'][i]
                    opt_code = self.opts_code[var_opt['id']]
                    pv = CAT[f"product.{product_key}.{variant_key}.option.{opt_code}"]
                    gr.add( (pv, RDF['type'], SCH['PropertyValue']) )
                    gr.add( (pv, SCH['propertyID'], self.opts_uri[var_opt['id']]) )
                    gr.add( (pv, SCH['value'], self.opts_ids[var_opt['id']]) )
                    gr.add( (model, SCH['additionalProperty'], pv) )
                offer = CAT[f"product.{product_key}.{variant_key}.offer"]
                gr.add( (offer, RDF['type'], SCH['Offer']) )
                gr.add( (model, SCH['offers'], offer) )
                # Base Price
                price = Decimal(var_data['price']) / Decimal(100)
                gr.add( (offer, SCH['price'], Literal(price.quantize(Decimal('.01'), rounding=ROUND_DOWN))) )
                gr.add( (offer, SCH['priceCurrency'], Literal(var_data['currencyCode'])) )
        gr.add( (item, SCH['image'], Literal(detail['product']['featuredAsset']['preview'])) )
        gr.add( (item, SCH['description'], Literal(detail['product']['description'])) )
        term = CAT['terms.products.' + detail['product']['slug']]
        gr.add( (term, RDF['type'], SCH['DefinedTerm']) )
        dts = self.terms_product_slug
        gr.add( (term, SCH['inDefinedTermSet'], dts) )
        gr.add( (dts, SCH['hasDefinedTerm'], term) )
        gr.add( (term, SCH['termCode'], Literal(detail['product']['slug'])) )
        gr.add( (item, ATX['Product.slug'], term) )
        if 'customFields' in detail['product'] and detail['product']['customFields']['atellixUrl']:
            categories = detail['product']['customFields']['atellixUrl']
            for cat in sorted(categories):
                gr.add( (item, SCH['additionalType'], URIRef(cat)) )
        if link_collections:
            for col in detail['product']['collections']:
                cid = col['id']
                pid = detail['product']['id']
                curi = CAT[f"catalog.{cid}"]
                tqnode = CAT[f"catalog.{cid}.{pid}"]
                gr.add( (tqnode, RDF['type'], SCH['TypeAndQuantityNode']) )
                gr.add( (tqnode, SCH['typeOfGood'], item) )
                # Static data
                #gr.add( (tqnode, SCH['amountOfThisGood'], Literal(1)) )
                gr.add( (tqnode, SCH['businessFunction'], URIRef('http://purl.org/goodrelations/v1#Sell')) )
                gr.add( (curi, SCH['includesObject'], tqnode) )
        return item_uuid
