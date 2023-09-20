import Vue from 'vue'
import { ActionTree, GetterTree, MutationTree } from 'vuex'
import { IProduct } from '~/interfaces/product'
import { IAddress } from '~/interfaces/address'
import { Cart, CartData, CartItem, CartItemOption, CartTotal, PaymentData } from '~/interfaces/cart'

export interface CartState extends Cart {
    payments?: PaymentData[]
}

function getDefaultState (): CartState {
    return {
        items: [],
        merchants: [],
        quantity: 0,
        subtotal: 0,
        totals: [],
        total: 0,
        payments: [],
        token: '',
        tokenQuote: 0,
    }
}

export const state = getDefaultState

export interface CartItemQuantity {
    itemId: string
    value: number
}

export type CartGetPayload = {
    cart?: CartData
}

export type CartAddPayload = {
    product: IProduct
    options?: CartItemOption[]
    quantity?: number
    cart?: CartData
}

export type CartRemovePayload = {
    itemId: string
    cart?: CartData
}

export type CartUpdateQuantitiesPayload = {
    itemQuantity: CartItemQuantity[]
    cart?: CartData
}

export type SetShippingPayload = {
    cart?: CartData
}

export type PrepareCheckoutPayload = {
    payments?: PaymentData[]
    paymentMethod: { [key: string]: string }
    shippingAddress?: IAddress
    billingAddress?: IAddress
}

export type CheckoutCompletePayload = {
    cart?: CartData
}

export interface UpdateTokenInfo {
    token: string
    tokenQuote: number
}

function calcTotals (cart: CartData): CartTotal[] {
    if (cart.items.length === 0) {
        return []
    }
    var res: CartTotal[] = []
    if (cart.shipping > 0) {
        res.push({
            type: 'shipping',
            title: 'Shipping',
            price: cart.shipping
        })
    }
    if (cart.tax > 0) {
        res.push({
            type: 'tax',
            title: 'Tax',
            price: cart.tax,
        })
    }
    return res
}

// noinspection JSUnusedGlobalSymbols
export const mutations: MutationTree<CartState> = {
    getCart (state, payload: CartGetPayload) {
        const { cart } = payload
        const cartData: CartData = cart as CartData
        state.items = cartData.items
        state.merchants = cartData.merchants
        state.quantity = cartData.quantity
        state.subtotal = cartData.subtotal
        state.totals = calcTotals(cartData)
        state.total = cartData.total
    },
    add (state, payload: CartAddPayload) {
        const { cart, product, options = [], quantity = 1 } = payload
        const cartData: CartData = cart as CartData
        state.items = cartData.items
        state.merchants = cartData.merchants
        state.quantity = cartData.quantity
        state.subtotal = cartData.subtotal
        state.totals = calcTotals(cartData)
        state.total = cartData.total
        Vue.notify({
            type: 'success',
            text: `${product.name} added to cart!`
        })
    },
    remove (state, payload: CartRemovePayload) {
        const { cart, itemId } = payload
        const cartData: CartData = cart as CartData
        state.items = cartData.items
        state.merchants = cartData.merchants
        state.quantity = cartData.quantity
        state.subtotal = cartData.subtotal
        state.totals = calcTotals(cartData)
        state.total = cartData.total
    },
    updateQuantities (state, payload: CartUpdateQuantitiesPayload) {
        const { cart, itemQuantity } = payload
        const cartData: CartData = cart as CartData
        state.items = cartData.items
        state.merchants = cartData.merchants
        state.quantity = cartData.quantity
        state.subtotal = cartData.subtotal
        state.totals = calcTotals(cartData)
        state.total = cartData.total
    },
    setShipping (state, payload: SetShippingPayload) {
        const { cart } = payload
        const cartData: CartData = cart as CartData
        state.items = cartData.items
        state.merchants = cartData.merchants
        state.quantity = cartData.quantity
        state.subtotal = cartData.subtotal
        state.totals = calcTotals(cartData)
        state.total = cartData.total
    },
    prepareCheckout (state, payload: PrepareCheckoutPayload) {
        const { payments } = payload
        state.payments = payments as PaymentData[]
    },
    checkoutComplete (state, payload: CheckoutCompletePayload) {
        const { cart } = payload
        const cartData: CartData = cart as CartData
        state.items = cartData.items
        state.merchants = cartData.merchants
        state.quantity = cartData.quantity
        state.subtotal = cartData.subtotal
        state.totals = calcTotals(cartData)
        state.total = cartData.total
    },
    updateTokenInfo (state, payload: UpdateTokenInfo) {
        state.token = payload.token
        state.tokenQuote = payload.tokenQuote
    }
}

// noinspection JSUnusedGlobalSymbols
export const actions: ActionTree<CartState, {}> = {
    async getCart ({ state, commit }, payload: CartGetPayload): Promise<void> {
        const result = await this.$shopApi.getCart()
        payload.cart = result.cart as CartData
        commit('getCart', payload)
    },
    async add ({ state, commit }, payload: CartAddPayload): Promise<void> {
        const result = await this.$shopApi.addCartItem(payload.product, payload.quantity)
        payload.cart = result.cart as CartData
        commit('add', payload)
    },
    async remove ({ state, commit }, payload: CartRemovePayload): Promise<void> {
        const result = await this.$shopApi.removeCartItem(payload.itemId)
        payload.cart = result.cart as CartData
        commit('remove', payload)
    },
    async updateQuantities ({ state, commit }, payload: CartUpdateQuantitiesPayload): Promise<void> {
        for (var i = 0; i < payload.itemQuantity.length; i++) {
            const itemQty = payload.itemQuantity[i]
            const result = await this.$shopApi.updateCartItem(itemQty.itemId, itemQty.value)
            payload.cart = result.cart as CartData
        }
        commit('updateQuantities', payload)
    },
    async setShipping ({ state, commit }, payload: SetShippingPayload): Promise<void> {
        const result = await this.$shopApi.setShipping()
        payload.cart = result.cart as CartData
        commit('setShipping', payload)
    },
    async prepareCheckout ({ state, commit }, payload: PrepareCheckoutPayload): Promise<void> {
        var spec: any = {}
        spec['paymentMethod'] = payload.paymentMethod
        if (payload.shippingAddress) {
            spec['shippingAddress'] = payload.shippingAddress
        }
        if (payload.billingAddress) {
            spec['billingAddress'] = payload.billingAddress
        }
        const result = await this.$shopApi.prepareCheckout(spec)
        payload.payments = result.payments as PaymentData[]
        commit('prepareCheckout', payload)
    },
    async checkoutComplete ({ state, commit }, payload: CheckoutCompletePayload): Promise<void> {
        const result = await this.$shopApi.checkoutComplete()
        payload.cart = result.cart as CartData
        commit('checkoutComplete', payload)
    }
}

export const getters: GetterTree<CartState, {}> = {
    quantity (store) {
        return store.quantity
    }
}

