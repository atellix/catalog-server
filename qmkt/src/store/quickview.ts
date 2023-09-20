import { ActionTree, MutationTree } from 'vuex'
import { IProduct } from '~/interfaces/product'

export interface QuickviewState {
    open: boolean;
    product: IProduct | null;
}

interface QuickviewOpenPayload {
    product: IProduct;
}

interface QuickviewOpenSuccessPayload {
    product: IProduct;
}

function getDefaultState (): QuickviewState {
    return {
        open: false,
        product: null
    }
}

export const state = getDefaultState

// noinspection JSUnusedGlobalSymbols
export const mutations: MutationTree<QuickviewState> = {
    openSuccess (state, payload: QuickviewOpenSuccessPayload): void {
        state.open = true
        state.product = payload.product
    },
    close (state) {
        state.open = false
    }
}

let cancelPreviousRequest = () => {}

// noinspection JSUnusedGlobalSymbols
export const actions: ActionTree<QuickviewState, {}> = {
    async open ({ commit }, payload: QuickviewOpenPayload) {
        cancelPreviousRequest()

        await new Promise<void>((resolve) => {
            let canceled = false
            // sending request to server, timeout is used as a stub
            const timer = setTimeout(() => {
                console.log('product: ' + JSON.stringify(payload.product, null, 4))
                this.$shopApi.getProductBySlug(payload.product.id).then((product) => {
                    if (canceled) {
                        return
                    }

                    if (product) {
                        commit('openSuccess', { product })
                    }

                    resolve()
                })
            }, 350)

            cancelPreviousRequest = () => {
                canceled = true
                clearTimeout(timer)
                resolve()
            }
        })
    }
}
