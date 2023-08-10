import json
import uuid
import pprint
from html_sanitizer import Sanitizer
from decimal import Decimal, ROUND_DOWN
from rdflib import Graph, Literal, URIRef, Namespace, BNode
from rdflib.namespace import RDF, SKOS, RDFS, XSD, OWL, DC, DCTERMS

SCH = Namespace('http://schema.org/')
ATX = Namespace('http://rdf.atellix.net/1.0/schema/catalog/')

from util.media_cache import MediaCache

class VendureRecordBuilder(object):
    def __init__(self, vendure_client, gr, base_uri):
        self.vendure_client = vendure_client
        self.graph = gr
        self.lists = {}
        self.opts_ids = {}
        self.opts_uri = {}
        self.opts_code = {}
        self.opts_group_ids = {} # Remove with original 'build_product' function
        self.CAT = Namespace(base_uri)
        dts = self.CAT['terms.products']
        gr.add( (dts, RDF['type'], SCH['DefinedTermSet']) )
        gr.add( (dts, SCH['identifier'], Literal('slug')) )
        self.terms_product_slug = dts

    def build_list(self):
        CAT = self.CAT
        gr = self.graph
        itemlist = CAT['list.' + str(uuid.uuid4())]
        self.lists[str(itemlist)] = 0
        gr.add( (itemlist, RDF['type'], SCH['ItemList']) )
        return itemlist

    def add_to_list(self, itemlist, val):
        CAT = self.CAT
        gr = self.graph
        ct = self.lists[str(itemlist)]
        item = CAT['item.' + str(uuid.uuid4())]
        gr.add( (itemlist, SCH['itemListElement'], item) )
        gr.add( (item, RDF['type'], SCH['ListItem']) )
        gr.add( (item, SCH['position'], Literal(ct)) )
        gr.add( (item, SCH['item'], val) )
        self.lists[str(itemlist)] = ct + 1
        return item

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
            take=1000,
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

    def build_product_spec(self, detail, merchant_uri, user_id):
        CAT = self.CAT
        term_sets = []
        product_key = detail['product']['id']
        item = CAT[f"product.{product_key}"]
        mc = MediaCache(user_id)
        preview_url = detail['product']['featuredAsset']['preview']
        image_url = mc.import_url(preview_url)
        descr = detail['product']['description']
        hts = Sanitizer({
            'tags': ('h1', 'h2', 'h3', 'strong', 'em', 'p', 'ul', 'ol', 'li', 'br', 'sub', 'sup', 'hr'),
            'empty': ('p', 'br', 'hr'),
            'separate': ('h1', 'h2', 'h3', 'strong', 'em', 'p', 'ul', 'ol', 'li', 'sub', 'sup'),
            'attributes': {},
        })
        descr = hts.sanitize(descr)
        spec = {
            'id': str(item),
            'alternateName': detail['product']['slug'],
            'name': detail['product']['name'],
            'image': {
                'url': image_url,
            },
            'description': descr,
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

