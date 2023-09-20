import { MutationTree } from 'vuex'

export interface WalletState {
    connected: boolean
    publicKey: string
}

function getDefaultState (): WalletState {
    return {
        connected: false,
        publicKey: '',
    }
}

export const state = getDefaultState

// noinspection JSUnusedGlobalSymbols
export const mutations: MutationTree<WalletState> = {
    setWalletState (state, payload: WalletState) {
        state.connected = payload.connected
        state.publicKey = payload.publicKey
    },
}

