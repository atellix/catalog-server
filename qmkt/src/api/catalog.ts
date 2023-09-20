import { Result } from '@badrap/result'
import { ILink } from '~/interfaces/menus/link'
import { IProduct, IProductsList, IProductAttribute, IProductAttributeValue, IProductAttributeSelect } from '~/interfaces/product'
import { IShopCategory } from '~/interfaces/category'
import { IMerchant } from '~/interfaces/merchant'

import parsePhoneNumber from 'libphonenumber-js'
import { QueryEngine } from '@comunica/query-sparql-rdfjs'
import type { Term, Quad, DatasetCore } from '@rdfjs/types'

import {
    ObjectBuilder,
    abstractDefinitionMap,
    graphToJsonld,
    IProduct as CProduct,
    IProductGroup as CProductGroup,
    IMediaObject as CMediaObject,
} from '@atellix/catalog'

type IProductKey = keyof IProduct

const JsonLdParser = require('jsonld-streaming-parser').JsonLdParser
const N3 = require('n3')
const { DataFactory } = N3
const { namedNode, literal, defaultGraph, quad } = DataFactory
const Builder = new ObjectBuilder(abstractDefinitionMap)

function RDF(uriPart: string) { return namedNode('http://www.w3.org/1999/02/22-rdf-syntax-ns#' + uriPart) }
function SCH(uriPart: string) { return namedNode('http://schema.org/' + uriPart) }
function PRD(uriPart: string) { return namedNode('http://rdf.atellix.com/schema/catalog/Product/' + uriPart) }

function parseJsonLD(rdfData: string): Promise<DatasetCore> {
    return new Promise((resolve, reject) => {
        const parser = new JsonLdParser()
        const store = new N3.Store()
        parser
            .on('end', () => resolve(store))
            .on('data', (quad: Quad) =>  store.addQuad(quad))
            .on('error', (error: any) => reject(error))
        parser.write(rdfData)
        parser.end()
    })
}

function copyValues(source: any, fields: string[], result: any) {
    for (var i = 0; i < fields.length; i++) {
        const k = fields[i]
        if (k in source) {
            result[k] = source[k]
        }
    }
}

function decodeProductObject(store: DatasetCore, obj: any): Result<IProduct> {
    //console.log(JSON.stringify(obj, null, 4))
    var vq
    var record: { [key: string]: any } = { images: [] }
    // Get Product fields
    const fields = [
        'name',
        'description',
        'sku',
    ]
    copyValues(obj, fields, record)

    // Slug
    /*if ('alternateName' in obj && obj.alternateName.length > 0) {
        record.slug = obj.alternateName[0]
    }*/
    if ('slug' in obj) {
        record.slug = obj.slug
    }
    if ('identifier' in obj) {
        record.identifier = obj.identifier
    }

    // Get Offer
    if (obj.offers.length !== 1) {
        return Result.err(new Error('Invalid product offer'))
    }
    const offerFields = [
        'price',
        'availability',
    ]
    copyValues(obj.offers[0], offerFields, record)
    if ('offeredBy' in obj.offers[0] && 'name' in obj.offers[0].offeredBy) {
        record.merchant = obj.offers[0].offeredBy.name
    }

    if (!('price' in obj)) {
        //console.log(obj.offers[0])
        if ('priceSpecification' in obj.offers[0] && 'minPrice' in obj.offers[0].priceSpecification) {
            record.price = obj.offers[0].priceSpecification.minPrice
        }
    }

    // TODO: Get Brand
    const brand = null

    // Get Images
    if ('image' in obj) {
        record.images = obj.image.map((img: CMediaObject) => ('url' in img) ? img.url : img.id)
    }

    // Get Attributes
    if ('additionalProperty' in obj) {
        var attributes: any[] = []
        for (var i = 0; i < obj.additionalProperty.length; i++) {
            attributes.push(decodeProductAttribute(store, obj.additionalProperty[i]).unwrap())
        }
        record.attributes = attributes
    }

    //console.log('Record')
    //console.log(record)
    return Result.ok({
        id: record.identifier ?? '',
        uri: obj.id,
        name: record.name ?? '',
        sku: record.sku ?? '',
        slug: record.slug ?? '',
        images: record.images,
        price: Number(record.price),
        compareAtPrice: null,
        brand: brand,
        badges: [],
        categories: [],
        rating: 0,
        reviews: 0,
        attributes: record.attributes ?? '',
        description: record.description ?? '',
        availability: record.availability ?? '',
        variants: [],
        merchant: record.merchant ?? '',
        categoryPath: [],
    })
}

function decodeProduct(store: DatasetCore, obj: any, path: ILink[]): Result<IProduct> {
    const product = decodeProductObject(store, obj).unwrap()
    product.categoryPath = path
    if (obj.type === 'IProductGroup') {
        const copyKeys = [
            'name', 
            'description',
            'slug',
            'sku',
            'images',
            'brand',
            'price',
            'compareAtPrice',
            'categoryPath',
            'merchant',
        ]
        for (var i = 0; i < obj.hasVariant.length; i++) {
            var productVariant: any = decodeProductObject(store, obj.hasVariant[i]).unwrap()
            for (var j = 0; j < copyKeys.length; j++) {
                var key: IProductKey = copyKeys[j] as IProductKey
                var value: any = productVariant[key]
                if (product[key] !== null) {
                    if (value instanceof Array && value.length === 0 && (product[key] as Array<any>).length > 0) {
                        productVariant[key] = product[key]
                    } else if (value === '' && product[key] !== '') {
                        productVariant[key] = product[key]
                    } else if (value === null && product[key] !== null) {
                        productVariant[key] = product[key]
                    }
                }
            }
            product.variants.push(productVariant)
        }
        if (product.variants.length > 0) {
            product.price = product.variants[0].price
        }
    }
    //console.log('Final Product:')
    //console.log(product)
    return Result.ok(product as IProduct)
}

function decodeProductAttribute(store: DatasetCore, obj: any): Result<IProductAttribute> {
    var prop: { [key: string]: any } = {}
    // TODO: Caching
    copyValues(obj, ['identifier'], prop)
    copyValues(obj.propertyID, ['name', 'alternateName'], prop)
    if ('alternateName' in prop) {
        prop.alternateName = prop.alternateName[0]
    }
    prop.termset = obj.propertyID.id
    const termset = Builder.decodeResource(store, obj.propertyID.id, {})
    const valueList = termset.hasDefinedTerm
    var values: IProductAttributeValue[] = []
    for (var i = 0; i < valueList.length; i++) {
        var valueData: { [key: string]: any } = {}
        copyValues(valueList[i], ['name', 'alternateName', 'identifier'], valueData)
        const valueResult: IProductAttributeValue = {
            id: valueData.identifier ?? '',
            uri: valueList[i].id,
            name: valueData.name ?? '',
            slug: (valueData.alternateName.length > 0) ? valueData.alternateName[0] : '',
            active: valueList[i].id == obj.value.id,
        }
        values.push(valueResult)
    }
    const result: IProductAttribute = {
        id: prop.identifier ?? '',
        uri: obj.id,
        name: prop.name ?? '',
        slug: prop.alternateName ?? '',
        termset: prop.termset,
        values: values,
    }
    return Result.ok(result)
}

function decodeMerchant(obj: any): Result<IMerchant> {
    var record: { [key: string]: any } = {}
    if (obj.offers.length !== 1) {
        return Result.err(new Error('Invalid product offer'))
    }
    const orgFields = [
        'name',
        'email',
        'telephone',
        'sameAs',
    ]
    copyValues(obj.offers[0].offeredBy, orgFields, record)
    if (record.sameAs) {
        record.sameAs = record.sameAs.map((rc: any) => rc.id)
    }

    // Get PostalAddress fields
    if ('address' in obj.offers[0].offeredBy) {
        const addressFields = [
            'streetAddress',
            'addressLocality',
            'addressRegion',
            'postalCode',
            'addressCountry',
        ]
        copyValues(obj.offers[0].offeredBy.address, addressFields, record)
    }
    if (record.email && record.email.startsWith('mailto:')) {
        record.email = record.email.slice(7) // remove "mailto:" prefix
    }
    // Get ContactPoint fields
    if ('contactPoint' in obj.offers[0].offeredBy) {
        if ('hoursAvailable' in obj.offers[0].offeredBy.contactPoint[0]) {
            record.hours = obj.offers[0].offeredBy.contactPoint[0].hoursAvailable.description
        }
    }
    const country = 'US' // TODO: make this dynamic
    if (record.telephone) {
        var phone = record.telephone
        if (phone.startsWith('tel:')) {
            phone = phone.slice(4) // remove "tel:" prefix
        }
        const phoneNum = parsePhoneNumber(phone, country)
        if (phoneNum && phoneNum.isValid()) {
            record.telephone = phoneNum.formatNational()
        }
    }
    return Result.ok({
        name: record.name ?? '',
        address: record.streetAddress ?? '',
        city: record.addressLocality ?? '',
        region: record.addressRegion ?? '',
        postalCode: record.postalCode ?? '',
        country: record.addressCountry ?? '',
        email: record.email,
        phone: record.telephone,
        url: record.url,
        hours: record.hours ?? '',
        links: record.sameAs ?? [],
    })
}

export async function getProductUriByAttributes(graph: any, current: IProductAttribute[], select: IProductAttributeSelect): Promise<string> {
    var findProps: Array<{ prop: string, val: string}> = []
    for (var i = 0; i < current.length; i++) {  
        const attr = current[i]
        if (attr.uri === select.attributeUri) {
            findProps.push({ prop: attr.termset as string, val: select.valueUri })
        } else {
            for (var j = 0; j < attr.values.length; j++) {
                if (attr.values[j].active) {
                    findProps.push({ prop: attr.termset as string, val: attr.values[j].uri })
                }
            }
        }
    }
    var qry: string = ''
    for (var k = 0; k < findProps.length; k++) {
        qry = qry + "?prod <http://schema.org/additionalProperty> ?il" + k + ".\n"
        qry = qry + "?il" + k + " <http://schema.org/itemListElement> ?li" + k + ".\n"
        qry = qry + "?li" + k + " <http://schema.org/item> ?pv" + k + ".\n"
        qry = qry + "?pv" + k + " <http://schema.org/propertyID> <" + findProps[k].prop + ">.\n"
        qry = qry + "?pv" + k + " <http://schema.org/value> <" + findProps[k].val + ">.\n"
    }
    const stmt: string = "SELECT ?prod WHERE { " + qry + " } LIMIT 1"
    const engine = new QueryEngine()
    const bindStream = await engine.queryBindings(stmt, { sources: [graph] })
    const queryResult = await bindStream.toArray()
    var result = ''
    if (queryResult.length > 0) {
        result = queryResult[0].get('prod')?.value as string
    }
    return result
}

function iterateShopCategory(obj: any): Result<IShopCategory> {
    var children: IShopCategory[] = []
    var cat: IShopCategory = {
        type: 'shop',
        name: obj.name,
        id: parseInt(obj.identifier),
        slug: obj.alternateName[0],
        image: '',
        customFields: {},
        children: children,
    }
    if ('image' in obj) {
        cat.image = obj.image[0].id
    }
    if ('narrower' in obj) {
        for (var i = 0; i < obj.narrower.length; i++) {
            children.push(iterateShopCategory(obj.narrower[i]).unwrap())
        }
    }
    return Result.ok(cat)
}

function decodeShopCategories(obj: any): Result<IShopCategory[]> {
    var cts: IShopCategory[] = []
    for (var i = 0; i < obj.memberList.length; i++) {
        cts.push(iterateShopCategory(obj.memberList[i]).unwrap())
    }
    return Result.ok(cts)
}

function decodeProductList(store: DatasetCore, obj: any, options: any): Result<IProductsList> {
    const items: any[] = []
    const filters: any[] = []
    const page = options.page || 1
    const limit = options.limit || 10
    const sort = options.sort || 'default'
    //console.log(obj)
    if ('memberList' in obj) {
        obj.memberList.forEach((item: any) => {
            items.push(decodeProductObject(store, item).unwrap())
        })
    }
    const total = options.total || items.length
    const pages = Math.ceil(total / limit)
    const from = (page - 1) * limit + 1
    const to = Math.max(Math.min(page * limit, total), from)
    const pl: IProductsList = {
        page,
        limit,
        sort,
        total,
        pages,
        from,
        to,
        items,
        filters: filters.map(x => x.build())
    }
    //console.log(pl)
    return Result.ok(pl)
}

export async function decodeJsonLD (input: Promise<any>): Promise<{ store: DatasetCore, input: any}> {
    const inputData = await input
    const jsonData = JSON.stringify(inputData.graph)
    const store = await parseJsonLD(jsonData)
    return { store: store, input: inputData }
}

export function decodeObject(store: DatasetCore, uuid: string): any {
    const mainId = Builder.getUriForUUID(store, uuid)
    //console.log(mainId)
    if (mainId) {
        return Builder.decodeResource(store, mainId, {})
    }
    return null
}

export function decodeLinkPath (path: any[]): ILink[] {
    var linkPath: ILink[] = []
    path.forEach((p) => {
        linkPath.push({
            'title': p.name,
            'url': '/category/' + p.key,
        })
    })
    return linkPath
}

export async function getRequest (input: Promise<any>): Promise<any> {
    const inputData = await input
    if (inputData['result'] === 'ok') {
        return inputData
    } else {
        return Promise.reject(inputData)
    }
}

export function getProduct (store: DatasetCore, obj: any, path: any[], productKey: string): IProduct {
    var productIndex: number = 0
    if (productKey.indexOf('.') >= 0) {
        const pts = productKey.split('.', 2)
        productKey = pts[0]
        productIndex = parseInt(pts[1])
    }
    const linkPath: ILink[] = decodeLinkPath(path)
    const product: IProduct = decodeProduct(store, obj, linkPath).unwrap()
    if (!product.id) {
        product.id = productKey
        for (var i = 0; i < product.variants.length; i++) {
            product.variants[i].id = productKey + '.' + i
            if (i === productIndex) {
                product.variants[i].selected = true
            }
        }
    }
    product.selected = productIndex
    //console.log(product)
    return product
}

export function getProductList (store: DatasetCore, obj: any, options: any): IProductsList {
    const plist: IProductsList = decodeProductList(store, obj, options).unwrap()
    return plist
}

export function getMerchant (obj: any): IMerchant {
    const merchant: IMerchant = decodeMerchant(obj).unwrap()
    return merchant
}

export function getShopCategories (obj: any): IShopCategory[] {
    const shopcts: IShopCategory[] = decodeShopCategories(obj).unwrap()
    return shopcts
}


