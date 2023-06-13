#!/usr/bin/env python3

import json
from string import Template
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

__all__ = [
    'VendureClient'
]

VendureElement = {}
VendureElement['ActiveOrder'] = """
fragment ActiveOrder on Order {
    id
    code
    state
    couponCodes
    subTotalWithTax
    shippingWithTax
    totalWithTax
    totalQuantity
    lines {
        id
        productVariant {
            id
            name
        }
        featuredAsset {
            id
            preview
        }
        quantity
        linePriceWithTax
    }
}
""".strip()
VendureElement['AssetFragment'] = """
fragment Asset on Asset {
    id
    width
    height
    name
    preview
    focalPoint {
        x
        y
    }
}
""".strip()
VendureElement['OrderAddressFragment'] = """
fragment OrderAddress on OrderAddress {
    fullName
    company
    streetLine1
    streetLine2
    city
    province
    postalCode
    country
    phoneNumber
}
""".strip()
VendureElement['CartFragment'] = Template("""
$AssetFragment
$OrderAddressFragment
fragment Cart on Order {
    id
    code
    state
    active
    customer {
        firstName
        lastName
        emailAddress
    }
    lines {
        id
        featuredAsset {
            ...Asset
        }
        unitPrice
        unitPriceWithTax
        quantity
        linePriceWithTax
        discountedLinePriceWithTax
        productVariant {
            sku
            id
            name
            options {
                id
                code
                name
                group {
                    name
                } 
            }
        }
        discounts {
            amount
            amountWithTax
            description
            adjustmentSource
            type
        }
    }
    totalQuantity
    subTotal
    subTotalWithTax
    total
    totalWithTax
    shipping
    shippingAddress {
        ...OrderAddress
    }
    billingAddress {
        ...OrderAddress
    }
    shippingWithTax
    shippingLines {
        priceWithTax
        shippingMethod {
            id
            code
            name
            description
        }
    }
    discounts {
        amount
        amountWithTax
        description
        adjustmentSource
        type
    }
    payments {
        method
        amount
        state
        transactionId
        errorMessage
        metadata
    }
}
""".strip()).safe_substitute(VendureElement)
VendureElement['ErrorResultFragment'] = """
fragment ErrorResult on ErrorResult {
    errorCode
    message
}
""".strip()
VendureElement['AddressFragment'] = """
fragment CustomerAddress on Address {
    id
    createdAt
    updatedAt
    fullName
    company
    streetLine1
    streetLine2
    city
    province
    postalCode
    country {
        name
        code
    }
    phoneNumber
    defaultShippingAddress
    defaultBillingAddress
}
""".strip()
VendureElement['CategoryCollection'] = """
	fragment CategoryCollection on Collection {
		id
		name
		slug
		featuredAsset {
            source
        }
		breadcrumbs {
			id
			name
			slug
		}
        customFields {
            atellixUrl
        }
	}
""".strip()
VendureElement['RecursiveCollections'] = Template("""
$CategoryCollection
fragment RecursiveCollections on Collection {
    parent {
        ...CategoryCollection
    }
    children {
        ...CategoryCollection
        children {
            ...CategoryCollection
            children {
                ...CategoryCollection
            }
        }
    }
}
""".strip()).safe_substitute(VendureElement)

class VendureClient(object):
    def __init__(self, url, auth_token=None):
        self.headers = {}
        if auth_token:
            self.headers['Authorization'] = 'Bearer {}'.format(auth_token)
        self.transport = RequestsHTTPTransport(url=url, **{'hooks': {'response': self.get_auth_token}, 'headers': self.headers})
        self.gql_client = Client(transport=self.transport, fetch_schema_from_transport=True)
        self.auth_token = auth_token

    def get_auth_token(self, r, *args, **kwargs):
        if 'vendure-auth-token' in r.headers:
            self.auth_token = r.headers['vendure-auth-token']
            self.headers['Authorization'] = 'Bearer {}'.format(self.auth_token)

    def gql_query(self, query, params, debug=False):
        if debug:
            print("Query: {}".format(query))
            print("Params: {}".format(params))
        return self.gql_client.execute(gql(query), variable_values=params)

    def admin_login(self, **data):
        params = {}
        params['username'] = data['username']
        params['password'] = data['password']
        params['rememberMe'] = data.get('rememberMe', False)
        qry = """
mutation login($username: String!, $password: String!, $rememberMe: Boolean) {
    login(username: $username, password: $password, rememberMe: $rememberMe) {
        ... on CurrentUser {
            id
            identifier
            channels {
                id
                token
                code
                permissions
            }
        }
        ... on InvalidCredentialsError {
            errorCode
            message
            authenticationError
        }
        ... on NativeAuthStrategyError {
            errorCode
            message
        }
    }
}
        """.strip()
        return self.gql_query(qry, params)
    
    def add_to_cart(self, pv, qty):
        params = {}
        params['productVariantId'] = pv
        params['quantity'] = qty
        qry = Template("""
$ActiveOrder
mutation AddItemToOrder($productVariantId: ID! $quantity: Int!) {
    addItemToOrder(productVariantId: $productVariantId, quantity: $quantity) {
        ... ActiveOrder
        ... on ErrorResult {
            errorCode
            message
        }
    }
}
""".strip()).safe_substitute(VendureElement)
        return self.gql_query(qry, params)

    def remove_from_cart(self, line):
        params = {}
        params['orderLineId'] = line
        qry = Template("""
$ActiveOrder
mutation RemoveOrderLine($orderLineId: ID!) {
    removeOrderLine(orderLineId: $orderLineId) {
        ... ActiveOrder
        ... on ErrorResult {
            errorCode
            message
        }
    }
}
""".strip()).safe_substitute(VendureElement)
        return self.gql_query(qry, params)

    def get_cart(self):
        qry = Template("""
$ActiveOrder
query ActiveOrder {
    activeOrder {
        ... ActiveOrder
    }
    nextOrderStates
    activeCustomer {
        id
    }
}
""".strip()).safe_substitute(VendureElement)
        return self.gql_query(qry, {})

    def set_customer(self, **data):
        params = {}
        for k in ['title', 'firstName', 'lastName', 'phoneNumber', 'emailAddress']:
            if k in data:
                params[k] = data[k]
        params['customFields'] = json.dumps({})
        qry = Template("""
$CartFragment
$ErrorResultFragment
mutation setCustomerForOrder($input: CreateCustomerInput!) {
    setCustomerForOrder(input: $input) {
        ...Cart
        ...ErrorResult
    }
}
""".strip()).safe_substitute(VendureElement)
        return self.gql_query(qry, {'input': params})

    def set_shipping_method(self, mth):
        params = {}
        params['shippingMethodId'] = mth
        qry = Template("""
$CartFragment
$ErrorResultFragment
mutation setOrderShippingMethod($shippingMethodId: ID!) {
    setOrderShippingMethod(shippingMethodId: $shippingMethodId) {
        ...Cart
        ...ErrorResult
    }
}
""".strip()).safe_substitute(VendureElement)
        return self.gql_query(qry, params)

    def set_payment_method(self, mcode, mdata={}):
        params = {}
        params['method'] = mcode
        params['metadata'] = json.dumps(mdata)
        qry = Template("""
$CartFragment
$ErrorResultFragment
mutation addPaymentToOrder($input: PaymentInput!) {
    addPaymentToOrder(input: $input) {
        ...Cart
        ...ErrorResult
    }
}
""".strip()).safe_substitute(VendureElement)
        return self.gql_query(qry, {'input': params})

    def verify_atellix_pay(self, code):
        params = {}
        qry = Template("""
mutation verifyAtellixPayOrder($code: String) {
    verifyAtellixPayOrder(code: $code)
}
""".strip()).safe_substitute(VendureElement)
        return self.gql_query(qry, {'code': code})

    def address_data(self, **data):
        params = {}
        for k in [
            'fullName',
            'company',
            'streetLine1',
            'streetLine2',
            'city',
            'province',
            'postalCode',
            'countryCode',
            'phoneNumber',
            'defaultShippingAddress',
            'defaultBillingAddress',
        ]:
            if k in data:
                params[k] = data[k]
            elif k == 'defaultShippingAddress' or k == 'defaultBillingAddress':
                params[k] = data.get(k, False)
            else:
                params[k] = ''
        params['customFields'] = json.dumps(data.get('customFields', {}))
        return params

#    def create_customer_address(self, **data):
#        params = self.address_data(**data)
#        qry = Template("""
#$AddressFragment
#mutation createCustomerAddress($input: CreateAddressInput!) {
#    createCustomerAddress(input: $input) {
#        ...CustomerAddress
#    }
#}
#""".strip()).safe_substitute(VendureElement)
#        return self.gql_query(qry, {'input': params}, True)

    def set_shipping_address(self, **data):
        params = self.address_data(**data)
        qry = Template("""
$CartFragment
$ErrorResultFragment
mutation setOrderShippingAddress($input: CreateAddressInput!) {
    setOrderShippingAddress(input: $input) {
        ...Cart
        ...ErrorResult
    }
}
""".strip()).safe_substitute(VendureElement)
        return self.gql_query(qry, {'input': params})

    def set_billing_address(self, **data):
        params = self.address_data(**data)
        qry = Template("""
$CartFragment
$ErrorResultFragment
mutation setOrderBillingAddress($input: CreateAddressInput!) {
    setOrderBillingAddress(input: $input) {
        ...Cart
        ...ErrorResult
    }
}
""".strip()).safe_substitute(VendureElement)
        return self.gql_query(qry, {'input': params})

    def set_state(self, st):
        params = {}
        params['state'] = st
        qry = Template("""
$CartFragment
$ErrorResultFragment
mutation transitionOrderToState($state: String!) {
    transitionOrderToState(state: $state) {
        ...Cart
        ...ErrorResult
    }
}
""".strip()).safe_substitute(VendureElement)
        return self.gql_query(qry, params)

    def get_category(self, **data):
        params = {}
        params['skip'] = data.get('skip', 0)
        params['take'] = data.get('take', 20)
        params['sort'] = data.get('sort', {})
        params['filter'] = data.get('filter', {})
        params['filterOperator'] = data.get('filterOperator', 'AND')
        qry = Template("""
$RecursiveCollections
query collections ($options: CollectionListOptions) {
    collections (options: $options) {
        totalItems
        items {
            ...CategoryCollection
            ...RecursiveCollections
        }
    }
}
""".strip()).safe_substitute(VendureElement)
        return self.gql_query(qry, {'options': params})

    def get_facets(self, **data):
        params = {}
        params['skip'] = data.get('skip', 0)
        params['take'] = data.get('take', 20)
        params['sort'] = data.get('sort', {})
        params['filter'] = data.get('filter', {})
        params['filterOperator'] = data.get('filterOperator', 'AND')
        qry = """
query facets ($options: FacetListOptions) {
    facets(options: $options) {
        totalItems
        items {
            id
            name
            code
            customFields {
                atellixUrl
            },
            values {
                id
                name
                code
                customFields {
                    atellixUrl
                }
                translations {
                    id
                    languageCode
                    name
                }
            }
            translations {
                id
                languageCode
                name
            }
        }
    }
}
        """.strip()
        return self.gql_query(qry, {'options': params})

    def set_facet(self, **data):
        params = {}
        params['code'] = data['code']
        if 'id' in data:
            params['id'] = data['id']
        if 'isPrivate' in data:
            params['isPrivate'] = data['isPrivate']
        if 'translations' in data:
            params['translations'] = data['translations']
        if 'customFields' in data:
            params['customFields'] = data['customFields']
        qry = """
mutation updateFacet ($input: UpdateFacetInput!) {
    updateFacet(input: $input) {
        id
        name
        code
        isPrivate
        customFields {
            atellixUrl
        }
        translations {
            id
            languageCode
            name
        }
    }
}
        """.strip()
        return self.gql_query(qry, {'input': params})

    def set_facet_value(self, **data):
        params = {}
        params['code'] = data['code']
        if 'id' in data:
            params['id'] = data['id']
        if 'translations' in data:
            params['translations'] = data['translations']
        if 'customFields' in data:
            params['customFields'] = data['customFields']
        qry = """
mutation updateFacetValues ($input: UpdateFacetValueInput!) {
    updateFacetValues(input: [$input]) {
        id
        name
        code
        customFields {
            atellixUrl
        }
        translations {
            id
            languageCode
            name
        }
    }
}
        """.strip()
        return self.gql_query(qry, {'input': params})

    def get_facet(self, **data):
        params = {}
        params['facetValueIds'] = data.get('facetValueIds', [])
        params['collectionSlug'] = data.get('collectionSlug', '')
        params['groupByProduct'] = data.get('groupByProduct', True)
        params['take'] = data.get('take', 20)
        params['skip'] = data.get('skip', 0)
        params['sort'] = data.get('sort', {})
        qry = Template("""
$RecursiveCollections
query search ($input: SearchInput!) {
    search(input: $input) {
        collections {
            collection {
                ...CategoryCollection
                ...RecursiveCollections
            }
        }
        totalItems
        items {
            sku
            slug
            productId
            productName
            productAsset {
                preview
            }
            productVariantId
            productVariantName
            productVariantAsset {
                preview
            }
            description
            currencyCode
            facetIds
            facetValueIds
            collectionIds
            price {
                ... on PriceRange {
                    min
                    max
                }
                ... on SinglePrice {
                    value
                }
            }
            priceWithTax {
                ... on PriceRange {
                    min
                    max
                }
                ... on SinglePrice {
                    value
                }
            }
        }
        facetValues {
            count
            facetValue {
                id
                name
                facet {
                    id
                    name
                }
            }
        }
    }
}
""".strip()).safe_substitute(VendureElement)
        return self.gql_query(qry, {'input': params})

    def get_product(self, pid, slug=None):
        params = {}
        params['id'] = pid
        if slug:
            params['slug'] = slug
        qry = Template("""
query product ($id: ID, $slug: String) {
    product(id: $id, slug: $slug) {
        id
        name
        slug
        description
        variants {
            id
            sku
            name
            price
            priceWithTax
            currencyCode
            options {
                id
                name
                code
            }
        }
        featuredAsset {
            preview
        }
        assets {
            preview
        }
        collections {
            id
            name
        }
        optionGroups {
            id
            name
            code
            options {
                id
                name
                code
            }
        }
        customFields {
            atellixUrl
        }
    }
}
""".strip()).safe_substitute(VendureElement)
        return self.gql_query(qry, params)
