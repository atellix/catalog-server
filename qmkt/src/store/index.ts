import { OffcanvasCartState } from '~/store/offcanvasCart'
import { MobileMenuState } from '~/store/mobileMenu'
import { OptionsState } from '~/store/options'
import { CurrencyState } from '~/store/currency'
import { QuickviewState } from '~/store/quickview'
import { WishlistState } from '~/store/wishlist'
import { CartState } from '~/store/cart'
import { LocaleState } from '~/store/locale'
import { ShopState } from '~/store/shop'

import Vue from 'vue'
import { MutationTree } from 'vuex'

export interface SocketState {
    socket: {
        message: string
        isConnected: boolean
        reconnectError: boolean
        closeEvent: any
    },
    oracleSubscr: { [key: string]: boolean }
}

function getDefaultState (): SocketState {
    return {
        socket: {
            message: '',
            isConnected: false,
            reconnectError: false,
            closeEvent: undefined
        },
        oracleSubscr: {}
    }
}

export const state = getDefaultState

// noinspection JSUnusedGlobalSymbols
export const mutations: MutationTree<SocketState> = {
    SOCKET_ONOPEN (state, event: any) {
        Vue.prototype.$socket = event.currentTarget
        state.socket.isConnected = true
    },
    SOCKET_ONCLOSE (state, event: any) {
        // console.log('WS Close')
        state.socket.isConnected = false
        state.socket.closeEvent = event
    },
    SOCKET_ONERROR (state, event: any) {
        // console.log('WS Error')
        console.error(state, event)
    },
    // default handler called for all methods
    SOCKET_ONMESSAGE (state, message: any) {
        state.socket.message = message
    },
    // mutations for reconnect methods
    SOCKET_RECONNECT (state, count: any) {
        //console.info('WS Reconnect')
        console.info(state, count)
    },
    SOCKET_RECONNECT_ERROR (state) {
        state.socket.reconnectError = true
    }
}

export interface RootState {
    websocket: SocketState;
    cart: CartState;
    offcanvasCart: OffcanvasCartState;
    mobileMenu: MobileMenuState;
    options: OptionsState;
    currency: CurrencyState;
    quickview: QuickviewState;
    wishlist: WishlistState;
    locale: LocaleState;
    shop: ShopState;
}
