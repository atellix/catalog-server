import json
import uuid
import pprint
from decimal import Decimal, ROUND_DOWN
from rdflib import Graph, Literal, URIRef, Namespace, BNode
from rdflib.namespace import RDF, SKOS, RDFS, XSD, OWL, DC, DCTERMS

SCH = Namespace('http://schema.org/')
ATX = Namespace('http://rdf.atellix.net/1.0/schema/catalog/')
CAT = Namespace('http://rdf.example.com/')

class VendureRecordBuilder(object):
    def __init__(self, vendure_client, gr):
        self.vendure_client = vendure_client
        self.graph = gr
        self.lists = {}
        self.opts_ids = {}
        self.opts_uri = {}
        self.opts_code = {}
        self.opts_group_ids = {} # Remove with original 'build_product' function
        dts = CAT['terms.products']
        gr.add( (dts, RDF['type'], SCH['DefinedTermSet']) )
        gr.add( (dts, SCH['identifier'], Literal('slug')) )
        self.terms_product_slug = dts

    def build_list(self):
        gr = self.graph
        itemlist = CAT['list.' + str(uuid.uuid4())]
        self.lists[str(itemlist)] = 0
        gr.add( (itemlist, RDF['type'], SCH['ItemList']) )
        return itemlist

    def add_to_list(self, itemlist, val):
        gr = self.graph
        ct = self.lists[str(itemlist)]
        item = CAT['item.' + str(uuid.uuid4())]
        gr.add( (itemlist, SCH['itemListElement'], item) )
        gr.add( (item, RDF['type'], SCH['ListItem']) )
        gr.add( (item, SCH['position'], Literal(ct)) )
        gr.add( (item, SCH['item'], val) )
        self.lists[str(itemlist)] = ct + 1
        return item

    def iter_catalog(self, cat_ids, cat_child, item_list, current_id):
        gr = self.graph
        cat_data = cat_ids[current_id]
        catrc = cat_data['uri']
        self.add_to_list(item_list, catrc)
        #print(cat_data)
        gr.add( (catrc, RDF['type'], SKOS['Concept']) )
        gr.add( (catrc, SCH['identifier'], Literal(cat_data['id'])) )
        gr.add( (catrc, SCH['name'], Literal(cat_data['name'])) )
        gr.add( (catrc, SCH['alternateName'], Literal(cat_data['slug'])) )
        if cat_data['image']:
            gr.add( (catrc, SCH['image'], URIRef(cat_data['image'])) )
        for url in cat_data['urls']:
            gr.add( (catrc, SCH['additionalType'], URIRef(url)) )
        if current_id in cat_child and len(cat_child[current_id]) > 0:
            next_list = self.build_list()
            gr.add( (catrc, SKOS['narrower'], next_list) )
            for nrc in cat_child[current_id]:
                self.iter_catalog(cat_ids, cat_child, next_list, nrc)
        
    # TODO: max depth
    def build_catalog(self, root_id=1):
        gr = self.graph
        catsch = CAT['catalog']
        item_uuid = str(uuid.uuid4())
        root_list = self.build_list()
        gr.add( (catsch, ATX['Object.uuid'], URIRef(f'urn:uuid:{item_uuid}')) )
        gr.add( (catsch, RDF['type'], SKOS['OrderedCollection']) )
        gr.add( (catsch, SKOS['memberList'], root_list) )
        vcl = self.vendure_client
        cts = vcl.get_category()
        cat_ids = {}
        cat_child = {}
        for category in cts['collections']['items']:
            #print(category)
            slug = category['slug']
            parent = category['parent']
            #print('{} -> {}: {}'.format(parent['id'], category['id'], slug))
            img = None
            if 'featuredAsset' in category:
                if 'source' in category['featuredAsset'] and len(category['featuredAsset']['source']) > 0:
                    img = category['featuredAsset']['source']
            cat_ids[category['id']] = {
                'id': category['id'],
                'name': category['name'],
                'image': img,
                'slug': category['slug'],
                'parent': category['parent']['id'],
                'urls': [],
            }
            if category['customFields']['atellixUrl'] is not None:
                cat_ids[category['id']]['urls'] = category['customFields']['atellixUrl']
            cat_child.setdefault(category['parent']['id'], [])
            cat_child[category['parent']['id']].append(category['id'])
        for cid in sorted(cat_ids.keys()):
            cat_data = cat_ids[cid]
            catrc = CAT[f"catalog.{cid}"]
            cat_data['uri'] = catrc
        for rc in cat_child[str(root_id)]:
            self.iter_catalog(cat_ids, cat_child, root_list, rc)
        return item_uuid

    def iter_catalog_categories(self, cat_ids, cat_child, cat_list, current_id):
        gr = self.graph
        cat_data = cat_ids[current_id]
        cat_list.append(cat_data)
        if current_id in cat_child and len(cat_child[current_id]) > 0:
            for nrc in cat_child[current_id]:
                self.iter_catalog_categories(cat_ids, cat_child, cat_list, nrc)
 
    # TODO: max depth
    def get_catalog_categories(self, merchant_uri, root_id=1):
        vcl = self.vendure_client
        gr = self.graph

        # Get merchant info
        mrch = {}
        for k in ['name', 'url', 'telephone', 'email', 'areaServed']:
            dv = gr.value(merchant_uri, SCH[k])
            if dv is not None:
                mrch[k] = str(dv)
                if k == 'telephone' and mrch[k].startswith('tel:'):
                    mrch[k] = mrch[k][4:]
                elif k == 'email' and mrch[k].startswith('mailto:'):
                    mrch[k] = mrch[k][7:]
        # Get collections
        cts = vcl.get_category()
        cat_ids = {}
        cat_child = {}
        cat_list = []
        for category in cts['collections']['items']:
            slug = category['slug']
            parent = category['parent']
            cat_ids[category['id']] = {
                'id': category['id'],
                'name': category['name'],
                'slug': category['slug'],
                'parent': category['parent']['id'],
                'urls': [],
            }
            if category['customFields']['atellixUrl'] is not None:
                cat_ids[category['id']]['urls'] = category['customFields']['atellixUrl']
            cat_child.setdefault(category['parent']['id'], [])
            cat_child[category['parent']['id']].append(category['id'])
        for rc in cat_child[str(root_id)]:
            self.iter_catalog_categories(cat_ids, cat_child, cat_list, rc)
        cat_map = {}
        for ct in cat_list:
            for u in ct['urls']:
                cat_map.setdefault(u, [])
                cat_map[u].append({
                    'name': ct['name'],
                    'merchant': mrch,
                    'collection': {
                        'id': ct['id'],
                        'slug': ct['slug'],
                    },
                })
        return cat_map

    def get_catalog_category(self, collection_slug):
        vcl = self.vendure_client
        #print(f'Get facet {collection_slug}')
        #print(json.dumps(citems, indent=2))
        citems = vcl.get_facet(
            collectionSlug=collection_slug,
            groupByProduct=True,
            take=5,
        )
        collections = []
        products = []
        facets = []
        for coll in citems['search']['collections']:
            collections.append(coll)
        for product in citems['search']['items']:
            for pk in ['price', 'priceWithTax']:
                if 'min' in product[pk] and product[pk]['min'] == product[pk]['max']:
                    product[pk]['value'] = product[pk]['min']
                    del product[pk]['min']
                    del product[pk]['max']
            products.append(product)
        for facet in citems['search']['facetValues']:
            facets.append(facet)
        return {
            'collections': collections,
            'products': products,
            'facets': facets,
            'count': citems['search']['totalItems'],
        }

    def build_product(self, detail, merchant_uri, link_collections=False, item_uuid=None):
        #print(detail)
        gr = self.graph
        product_key = detail['product']['id']
        item = CAT[f"product.{product_key}"]
        if item_uuid is None:
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
            variant_list = self.build_list()
            gr.add( (item, SCH['hasVariant'], variant_list) )
            for var_data in detail['product']['variants']:
                variant_key = var_data['id']
                model = CAT[f"product.{product_key}.{variant_key}"]
                list_item = self.add_to_list(variant_list, model)
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
                        terms_list = self.build_list()
                        gr.add( (opts_set, SCH['hasDefinedTerm'], terms_list) )
                        for opts_item in opts_grp['options']:
                            opts_val = CAT[f"terms.{opts_grp['code']}.{opts_item['code']}"]
                            self.add_to_list(terms_list, opts_val)
                            gr.add( (opts_val, RDF['type'], SCH['DefinedTerm']) )
                            gr.add( (opts_val, SCH['name'], Literal(opts_item['name'])) )
                            gr.add( (opts_val, SCH['identifier'], Literal(opts_item['id'])) )
                            gr.add( (opts_val, SCH['alternateName'], Literal(opts_item['code'])) )
                            self.opts_ids[opts_item['id']] = opts_val
                            self.opts_uri[opts_item['id']] = opts_set
                            self.opts_code[opts_item['id']] = opts_grp['code']
                options_list = self.build_list()
                gr.add( (model, SCH['additionalProperty'], options_list) )
                for i in range(len(var_data['options'])):
                    var_opt = var_data['options'][i]
                    opt_code = self.opts_code[var_opt['id']]
                    pv = CAT[f"product.{product_key}.{variant_key}.option.{opt_code}"]
                    self.add_to_list(options_list, pv)
                    gr.add( (pv, RDF['type'], SCH['PropertyValue']) )
                    gr.add( (pv, SCH['propertyID'], self.opts_uri[var_opt['id']]) )
                    gr.add( (pv, SCH['value'], self.opts_ids[var_opt['id']]) )
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

    def build_product_list(self, detail, collection_slug, merchant_uri):
        gr = self.graph
        item_uuid = str(uuid.uuid4())
        plist = CAT[f'product_list.{collection_slug}']
        root_list = self.build_list()
        gr.add( (plist, RDF['type'], SKOS['OrderedCollection']) )
        gr.add( (plist, ATX['Object.uuid'], URIRef(f'urn:uuid:{item_uuid}')) )
        gr.add( (plist, SKOS['memberList'], root_list) )
        gr.add( (plist, ATX['Collection.total'], Literal(detail['count'])) )
        gr.add( (plist, SCH['alternateName'], Literal(collection_slug)) )
        for product in detail['products']:
            product_key = product['productId']
            item = CAT[f"product.{product_key}"]
            self.add_to_list(root_list, item)
            gr.add( (item, RDF['type'], SCH['Product']) )
            gr.add( (item, SCH['name'], Literal(product['productName'])) )
            gr.add( (item, SCH['alternateName'], Literal(product['slug'])) )
            gr.add( (item, SCH['productID'], Literal(product['productVariantId'])) )
            gr.add( (item, SCH['sku'], Literal(product['sku'])) )
            gr.add( (item, SCH['image'], Literal(product['productAsset']['preview'])) )
            gr.add( (item, SCH['description'], Literal(product['description'])) )
            # Offer
            offer = CAT[f"product.{product_key}.offer"]
            gr.add( (item, SCH['offers'], offer) )
            gr.add( (offer, RDF['type'], SCH['Offer']) )
            gr.add( (offer, SCH['offeredBy'], merchant_uri) )
            # Base Price
            if 'value' in product['price']:
                price = Decimal(product['price']['value']) / Decimal(100)
                gr.add( (offer, SCH['price'], Literal(price.quantize(Decimal('.01'), rounding=ROUND_DOWN))) )
                gr.add( (offer, SCH['priceCurrency'], Literal(product['currencyCode'])) )
            else:
                min_price = Decimal(product['price']['min']) / Decimal(100)
                max_price = Decimal(product['price']['max']) / Decimal(100)
                spec_uuid = str(uuid.uuid4())
                pr_spec = CAT[f'price_spec.{spec_uuid}']
                gr.add( (offer, SCH['priceSpecification'], pr_spec) )
                gr.add( (pr_spec, RDF['type'], SCH['PriceSpecification']) ) 
                gr.add( (pr_spec, SCH['minPrice'], Literal(min_price.quantize(Decimal('.01'), rounding=ROUND_DOWN))) )
                gr.add( (pr_spec, SCH['maxPrice'], Literal(max_price.quantize(Decimal('.01'), rounding=ROUND_DOWN))) )
                gr.add( (pr_spec, SCH['priceCurrency'], Literal(product['currencyCode'])) )
        return item_uuid

    def build_product_spec(self, detail, merchant_uri):
        term_sets = []
        product_key = detail['product']['id']
        item = CAT[f"product.{product_key}"]
        spec = {
            'id': str(item),
            #'identifier': product_key,
            'alternateName': detail['product']['slug'],
            'name': detail['product']['name'],
            'image': {
                'url': detail['product']['featuredAsset']['preview'],
            },
            'description': detail['product']['description'],
        }
        if 'customFields' in detail['product'] and detail['product']['customFields']['atellixUrl']:
            categories = []
            for cat in sorted(detail['product']['customFields']['atellixUrl']):
                categories.append({'id': cat})
            spec['additionalType'] = categories
        var_ct = len(detail['product']['variants'])
        if var_ct == 1:
            var_data = detail['product']['variants'][0]
            spec['type'] = 'IProduct'
            spec['productID'] = var_data['id']
            spec['sku'] = var_data['sku']
            # Offer
            offer = CAT[f"product.{product_key}.offer"]
            # Base Price
            price = Decimal(var_data['price']) / Decimal(100)
            spec['offers'] = [{
                'id': str(offer),
                'offeredBy': {
                    'id': merchant_uri,
                    'type': 'IOrganization',
                },
                'price': price.quantize(Decimal('.01'), rounding=ROUND_DOWN),
                'priceCurrency': var_data['currencyCode'],
            }]
        else:
            spec['type'] = 'IProductGroup'
            # Main Offer
            offer = CAT[f"product.{product_key}.offer"]
            spec['offers'] = [{
                'id': str(offer),
                'offeredBy': {
                    'id': merchant_uri,
                    'type': 'IOrganization',
                },
            }]
            opts_seen = {}
            variant_list = []
            for var_data in detail['product']['variants']:
                variant_key = var_data['id']
                model = CAT[f"product.{product_key}.{variant_key}"]
                product = {
                    'id': model,
                    'type': 'IProduct',
                    'name': var_data['name'],
                    'productID': var_data['id'],
                    'sku': var_data['sku'],
                }
                # Options groups
                for opts_grp in detail['product']['optionGroups']:
                    if opts_grp['code'] in opts_seen:
                        continue
                    opts_seen[opts_grp['code']] = True
                    opts_set = CAT[f"terms.{opts_grp['code']}"]
                    # Build DefinedTermSet
                    terms_list = []
                    for opts_item in opts_grp['options']:
                        opts_val = CAT[f"terms.{opts_grp['code']}.{opts_item['code']}"]
                        dterm = {
                            'id': opts_val,
                            'type': 'IDefinedTerm',
                            'name': opts_item['name'],
                            'identifier': opts_item['id'],
                            'alternateName': opts_item['code'],
                        }
                        terms_list.append(dterm)
                        self.opts_ids[opts_item['id']] = opts_val
                        self.opts_uri[opts_item['id']] = opts_set
                        self.opts_code[opts_item['id']] = opts_grp['code']
                    dts = {
                        'id': opts_set,
                        'type': 'IDefinedTermSet',
                        'name': opts_grp['name'],
                        'identifier': opts_grp['id'],
                        'alternateName': opts_grp['code'],
                        'hasDefinedTerm': terms_list,
                    }
                    term_sets.append(dts)
                options_list = []
                for i in range(len(var_data['options'])):
                    var_opt = var_data['options'][i]
                    opt_code = self.opts_code[var_opt['id']]
                    pv = CAT[f"product.{product_key}.{variant_key}.option.{opt_code}"]
                    prop = {
                        'id': pv,
                        'type': 'IPropertyValue',
                        'propertyID': self.opts_uri[var_opt['id']],
                        'value': self.opts_ids[var_opt['id']],
                    }
                    options_list.append(prop)
                product['additionalProperty'] = options_list
                var_offer = CAT[f"product.{product_key}.{variant_key}.offer"]
                price = Decimal(var_data['price']) / Decimal(100)
                product['offers'] = [{
                    'id': str(var_offer),
                    'price': price.quantize(Decimal('.01'), rounding=ROUND_DOWN),
                    'priceCurrency': var_data['currencyCode'],
                }]
                variant_list.append(product)
            spec['hasVariant'] = variant_list
        result = [spec] + term_sets
        #pprint.pprint(result)
        return result

    def build_product_item_spec(self, detail):
        product_key = detail['productId']
        item = CAT[f"product.{product_key}"]
        offer = {}
        if 'min' in detail['price']:
            offer['priceCurrency'] = 'USD'
            offer['priceSpecification'] = {
                'minPrice': str(Decimal(detail['price']['min']) / Decimal(100)),
                'maxPrice': str(Decimal(detail['price']['max']) / Decimal(100)),
            }
        else:
            offer['price'] = str(Decimal(detail['price']['value']) / Decimal(100))
            offer['priceCurrency'] = 'USD'
        spec = {
            'id': str(item),
            'uuid': str(uuid.uuid4()),
            'type': 'IProduct',
            'name': detail['productName'],
            'identifier': detail['productId'],
            'description': detail['description'],
            'offers': [offer],
        }
        return spec

    def summarize_product_spec(self, product):
        summary = {
            'id': product['id'],
            'uuid': product['uuid'],
            'name': product['name'],
            'type': product['type'],
            'image': product['image'],
            'offers': [product['offers'][0]],
        }
        if product['type'] == 'IProductGroup':
            offer = summary['offers'][0].copy()
            offer.update(product['hasVariant'][0]['offers'][0])
            summary['offers'] = [offer]
        return summary

