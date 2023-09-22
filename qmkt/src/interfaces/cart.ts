import { IProduct } from './product'

export interface CartItemOption {
    optionId: number
    optionTitle: string
    valueId: number
    valueTitle: string
}

export type CartMerchant = {
    id: string
    label: string
    data: any
    index: number
}

export type CartItem = {
    id: string
    label: string
    image: string
    price: number
    quantity: number
    total: number
    options: CartItemOption[]
    merchant?: CartMerchant
}

export type CartData = {
    currency: string
    data: any
    items: CartItem[]
    merchants: CartMerchant[]
    count: number
    quantity: number
    subtotal: number
    shipping: number
    tax: number
    total: number
    complete: boolean
    cancel: boolean
    uuid?: string
}

export type CartTotalType = 'shipping' | 'tax'

export interface CartTotal {
    type: CartTotalType
    title: string
    price: number
}

export interface PaymentData {
    method: string
    total: number
    data: any
}

export interface Cart {
    items: CartItem[]
    merchants: CartMerchant[]
    quantity: number
    subtotal: number
    totals: CartTotal[]
    total: number
    token: string
    tokenQuote: number
    uuid?: string
}

