/* eslint-disable @typescript-eslint/no-unused-vars */
// noinspection JSUnusedLocalSymbols

import * as qs from 'qs'
import { Context, Plugin } from '@nuxt/types'
import { getCategories, getCategoryBySlug } from '~/fake-server/endpoints/categories'
import { CATALOG_HOST, ATELLIX_HOST } from './constants'
import { IFilterValues, IListOptions } from '~/interfaces/list'
import { IProduct, IProductsList } from '~/interfaces/product'
import { CartMerchant, CartItem, CartItemOption, CartData, PaymentData } from '~/interfaces/cart'
import { IShopCategory } from '~/interfaces/category'
import { IMerchant } from '~/interfaces/merchant'
import {
    getDiscountedProducts,
    getPopularProducts,
    getRelatedProducts,
    getTopRatedProducts
} from '~/fake-server/endpoints/products'
import {
    decodeJsonLD,
    decodeObject,
    getRequest,
    getProduct,
    getProductList,
    getMerchant,
    getShopCategories
} from '~/api/catalog'

export interface GetProductCollectionOptions {
    limit?: number;
    depth?: number;
}

export interface GetCategoriesOptions {
    depth?: number;
}

export interface GetCategoryBySlugOptions {
    depth?: number;
}

export interface GetRelatedProductsOptions {
    limit?: number;
}

export interface GetProductsOptions {
    limit?: number;
    category?: string;
}

export type GetSuggestionsOptions = {
    limit?: number;
    category?: string;
};

export type MerchantProduct = {
    product: IProduct;
    merchant: IMerchant;
    graph: any;
}

export type CartResult = {
    cart: CartData;
}

export type PrepareCheckoutResult = {
    payments: PaymentData[];
}

export type ProcessPaymentResult = {
    result: string;
    error?: string;
}

async function postData(url: string = "", data: any = {}): Promise<any> {
    const response = await fetch(url, {
        method: "POST",
        mode: "cors",
        cache: "no-cache",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        redirect: "manual",
        referrerPolicy: "no-referrer",
        body: JSON.stringify(data),
    })
    return response.json()
}

function decodeCartData(data: any): CartData {
    const merchants: CartMerchant[] = data.cart_items.merchants
    var items: CartItem[] = []
    data.cart_items.items.forEach((item: any) => {
        const rec: CartItem = {
            id: item.id,
            label: item.label,
            image: item.image ?? '',
            options: [], // TODO: item.options_data
            price: Number(item.price),
            quantity: Number(item.quantity),
            total: Number(item.total),
            merchant: merchants[item.merchant],
        }
        items.push(rec)
    })
    const cart: CartData = {
        'currency': data.cart_currency,
        'data': data.cart_data,
        'items': items,
        'merchants': merchants,
        'count': Number(data.cart_items.item_count),
        'quantity': Number(data.cart_items.item_quantity),
        'subtotal': Number(data.cart_subtotal),
        'shipping': Number(data.cart_shipping),
        'tax': Number(data.cart_tax),
        'total': Number(data.cart_total),
        'complete': data.checkout_complete == 1 ? true : false,
        'cancel': data.checkout_cancel == 1 ? true : false,
    }
    return cart
}

function getRequestURL(): string {
    return `https://${CATALOG_HOST}/api/catalog/commerce`
}

function getPaymentURL(path: string): string {
    return `https://${ATELLIX_HOST}/api/${path}`
}

/**
 * @param context Can be used, for example, to access the axios plugin.
 */
function make (context: Context) {
    return {
        getMerchantProduct: (productKey: string): Promise<MerchantProduct> => {
            var req: any = {
                'command': 'get_product',
                'key': productKey,
            }
            //console.log(context.route.params)
            if ('category' in context.route.params) {
                req['category'] = context.route.params.category
            }
            const url = getRequestURL()
            const result = decodeJsonLD(postData(url, req)).then((spec) => {
                const obj = decodeObject(spec.store, spec.input.uuid)
                return { product: getProduct(spec.store, obj, spec.input.path, productKey), merchant: getMerchant(obj), graph: spec.store }
            })
            return result
        },
        getProductBySlug: (slug: string): Promise<IProduct> => {
            var req: any = {
                'command': 'get_product',
                'key': slug,
            }
            if ('category' in context.route.params) {
                req['category'] = context.route.params.category
            }
            const url = getRequestURL()
            const result = decodeJsonLD(postData(url, req)).then((spec) => {
                const obj = decodeObject(spec.store, spec.input.uuid)
                return getProduct(spec.store, obj, spec.input.path, slug)
            })
            return result

        },
        getProductCollections: (merchantId: string, options: GetProductCollectionOptions): Promise<IShopCategory[]> => {
            const url = getRequestURL()
            const result = decodeJsonLD(postData(url, {
                'command': 'get_collection_list',
                'merchant': merchantId,
                'options': options,
            })).then((spec) => {
                const obj = decodeObject(spec.store, spec.input.uuid)
                return getShopCategories(obj)
            })
            return result
        },
        getProductURL: (path: string): string => {
            return `https://${CATALOG_HOST}${path}`
        },
        getCategoryBySlug: (slug: string, options: GetCategoryBySlugOptions = {}): Promise<IShopCategory> => {
            return getCategoryBySlug(slug, options)
        },
            /**
             * where:
             * - page            = options.page
             * - limit           = options.limit
             * - sort            = options.sort
             * - filter_category = filters.category
             * - filter_price    = filters.price
             */
        getProductsList: (options: IListOptions = {}, filters: IFilterValues = {}, search?: string): Promise<IProductsList> => {
            const url = getRequestURL()
            const result = decodeJsonLD(postData(url, {
                'command': 'get_product_list',
                'search': search,
                'options': options,
                'filters': filters,
            })).then((spec) => {
                const obj = decodeObject(spec.store, spec.input.uuid)
                return getProductList(spec.store, obj, {
                    'total': spec.input.count,
                    'limit': spec.input.limit,
                    'page': spec.input.page,
                })
            })
            return result
        },
        /**
         * Returns array of featured products.
         */
        getFeaturedProducts: (options: GetProductsOptions = {}): Promise<IProduct[]> => {
            const url = getRequestURL()
            const result = decodeJsonLD(postData(url, {
                'command': 'get_product_list',
                'edition': 'featured',
            })).then((spec) => {
                const obj = decodeObject(spec.store, spec.input.uuid)
                return getProductList(spec.store, obj, {}).items
            })
            return result
        },
        /**
         * Returns array of latest products.
         */
        getLatestProducts: (options: GetProductsOptions = {}): Promise<IProduct[]> => {
            const url = getRequestURL()
            const result = decodeJsonLD(postData(url, {
                'command': 'get_product_list',
                'edition': 'latest',
            })).then((spec) => {
                const obj = decodeObject(spec.store, spec.input.uuid)
                return getProductList(spec.store, obj, {}).items
            })
            return result
        },
        /**
         * Returns search suggestions.
         */
        getSuggestions: (query: string, options: GetSuggestionsOptions = {}): Promise<IProduct[]> => {
            const url = getRequestURL()
            const result = decodeJsonLD(postData(url, {
                'command': 'get_product_list',
                'search': query,
                'limit': options.limit,
            })).then((spec) => {
                const obj = decodeObject(spec.store, spec.input.uuid)
                return getProductList(spec.store, obj, {}).items
            })
            return result
        },
        /**
         * Get the current client's shopping cart
         */
        getCart: (): Promise<CartResult> => {
            const url = getRequestURL()
            const result = getRequest(postData(url, {
                'command': 'get_cart',
            })).then((data) => {
                return {
                    'cart': decodeCartData(data),
                }
            })
            return result
        },
        /**
         * Add an item to the current client's shopping cart, creates a new cart if necessary
         */
        addCartItem: (product: IProduct, quantity: number | undefined): Promise<CartResult> => {
            if (typeof(quantity) === 'undefined') {
                quantity = 1
            }
            const url = getRequestURL()
            const result = getRequest(postData(url, {
                'command': 'add_cart_item',
                'quantity': quantity,
                'key': product.id,
            })).then((data) => {
                return {
                    'cart': decodeCartData(data),
                }
            })
            return result
        },
        /**
         * Remove an item from the current client's shopping cart
         */
        removeCartItem: (productId: string): Promise<CartResult> => {
            const url = getRequestURL()
            const result = getRequest(postData(url, {
                'command': 'remove_cart_item',
                'key': productId,
            })).then((data) => {
                return {
                    'cart': decodeCartData(data),
                }
            })
            return result
        },
        /**
         * Update quantity or details of an item in the current client's shopping cart
         */
        updateCartItem: (productId: string, quantity: number): Promise<CartResult> => {
            const url = getRequestURL()
            const result = getRequest(postData(url, {
                'command': 'update_cart_item',
                'quantity': quantity,
                'key': productId,
            })).then((data) => {
                return {
                    'cart': decodeCartData(data),
                }
            })
            return result
        },
        /**
         * Set shipping
         */
        setShipping: (): Promise<CartResult> => {
            const url = getRequestURL()
            const result = getRequest(postData(url, {
                'command': 'set_shipping',
            })).then((data) => {
                return {
                    'cart': decodeCartData(data),
                }
            })
            return result
        },
        /**
         * Prepare cart for checkout
         */
        prepareCheckout: (spec: any): Promise<PrepareCheckoutResult> => {
            const url = getRequestURL()
            const result = getRequest(postData(url, {
                'command': 'prepare_checkout',
                'spec': spec,
            })).then((data) => {
                return {
                    'payments': data.payments as PaymentData[],
                }
            })
            return result
        },
        /**
         * Process AuthorizeNet payment
         */
        processAuthorizeNetPayment: (spec: any): Promise<ProcessPaymentResult> => {
            const url = getPaymentURL('payment_card/v1/authorizenet/payment')
            const result = getRequest(postData(url, spec)).then((data) => { return data })
            return result
        },
        /**
         * Finalize checkout
         */
        checkoutComplete: (): Promise<CartResult> => {
            const url = getRequestURL()
            const result = getRequest(postData(url, {
                'command': 'checkout_complete',
            })).then((data) => {
                return {
                    'cart': decodeCartData(data),
                }
            })
            return result
        },
        /**
         * Returns array of categories.
         */
        getCategories: (options: GetCategoriesOptions = {}): Promise<IShopCategory[]> => {
            /**
             * This is what your API endpoint might look like:
             *
             * https://example.com/api/categories.json?depth=2
             *
             * where:
             * - 2 = options.depth
             */
            // return fetch(`https://example.com/api/categories.json?${qs.stringify(options)}`)
            //     .then((response) => response.json());

            // This is for demonstration purposes only. Remove it and use the code above.
            return getCategories(options)
        },
        /**
         * Returns array of related products.
         */
        getRelatedProducts: (slug: string, options: GetRelatedProductsOptions = {}): Promise<IProduct[]> => {
            /**
             * This is what your API endpoint might look like:
             *
             * https://example.com/api/shop/products/screwdriver-a2017/related.json&limit=3
             *
             * where:
             * - screwdriver-a2017 = slug
             * - limit             = options.limit
             */
            // return fetch(`https://example.com/api/products/${slug}/related.json?${qs.stringify(options)}`)
            //     .then((response) => response.json());

            // This is for demonstration purposes only. Remove it and use the code above.
            return getRelatedProducts(slug, options)
        },
        /**
         * Return products list.
         */
        /**
         * Returns an array of top rated products.
         */
        getTopRatedProducts: (options: GetProductsOptions = {}): Promise<IProduct[]> => {
            /**
             * This is what your API endpoint might look like:
             *
             * https://example.com/api/shop/top-rated-products.json?limit=3&category=power-tools
             *
             * where:
             * - 3           = options.limit
             * - power-tools = options.category
             */
            // return fetch(`https://example.com/api/top-rated-products.json?${qs.stringify(options)}`)
            //     .then((response) => response.json());

            // This is for demonstration purposes only. Remove it and use the code above.
            return getTopRatedProducts(options)
        },
        /**
         * Returns an array of discounted products.
         */
        getDiscountedProducts: (options: GetProductsOptions = {}): Promise<IProduct[]> => {
            /**
             * This is what your API endpoint might look like:
             *
             * https://example.com/api/shop/discounted-products.json?limit=3&category=power-tools
             *
             * where:
             * - 3           = options.limit
             * - power-tools = options.category
             */
            // return fetch(`https://example.com/api/discounted-products.json?${qs.stringify(options)}`)
            //     .then((response) => response.json());

            // This is for demonstration purposes only. Remove it and use the code above.
            return getDiscountedProducts(options)
        },
        /**
         * Returns an array of most popular products.
         */
        getPopularProducts: (options: GetProductsOptions = {}): Promise<IProduct[]> => {
            /**
             * This is what your API endpoint might look like:
             *
             * https://example.com/api/shop/popular-products.json?limit=3&category=power-tools
             *
             * where:
             * - 3           = options.limit
             * - power-tools = options.category
             */
            // return fetch(`https://example.com/api/popular-products.json?${qs.stringify(options)}`)
            //     .then((response) => response.json());

            // This is for demonstration purposes only. Remove it and use the code above.
            return getPopularProducts(options)
        }
    }
}

declare module 'vue/types/vue' {
    interface Vue {
        $shopApi: ReturnType<typeof make> & Context
    }
}

declare module '@nuxt/types' {
    interface Context {
        $shopApi: ReturnType<typeof make> & Context
    }
}

declare module 'vuex/types/index' {
    interface Store<S> {
        $shopApi: ReturnType<typeof make> & Context,
    }
}

const plugin: Plugin = (context, inject) => {
    inject('shopApi', make(context))
}

export type ShopApi = ReturnType<typeof make>;

export default plugin
