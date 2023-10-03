import Vue from 'vue'
import { ActionTree, GetterTree, MutationTree } from 'vuex'
import { ICategory, IShopCategory } from '~/interfaces/category'
import { IProductsList } from '~/interfaces/product'
import { IFilterValues, IListOptions } from '~/interfaces/list'
import { IMerchant } from '~/interfaces/merchant'
import { IOrder } from '~/interfaces/order'
import { buildQuery } from '~/services/helpers'
import dataAccountOrderLoading from '~/data/accountOrderLoading'
import theme from '~/data/theme'

export interface ShopState {
    init: boolean;
    search: string | null;
    categorySlug: string | null;
    categoryIsLoading: boolean;
    category: ICategory | null;
    productsListIsLoading: boolean;
    productsList: IProductsList | null;
    options: IListOptions;
    filters: IFilterValues;
    query: string;
    merchant: IMerchant;
    receipt: IOrder;
}

export interface ShopInitPayload {
    search: string | null;
    categorySlug: string | null;
    options: IListOptions;
    filters: IFilterValues;
}

export interface FetchCategoryPayload {
    categorySlug: string | null;
}

export interface FetchCategorySuccessPayload {
    category: IShopCategory | null;
}

export interface FetchReceiptPayload {
    uuid: string;
}

export interface FetchReceiptSuccessPayload {
    receipt?: IOrder;
}

export interface FetchProductsListSuccessPayload {
    productsList: IProductsList;
}

export interface SetOptionValuePayload {
    option: keyof IListOptions;
    value: string | number;
}

export interface SetFilterValuePayload {
    filter: string;
    value: string | null;
}

export interface SetMerchantPayload {
    merchant: IMerchant;
}

function getDefaultState (): ShopState {
    return {
        init: false,
        search: null,
        categorySlug: null,
        categoryIsLoading: true,
        category: null,
        productsListIsLoading: true,
        productsList: null,
        options: {},
        filters: {},
        query: '',
        merchant: theme.merchant,
        receipt: dataAccountOrderLoading,
    }
}

export const state = getDefaultState

// noinspection JSUnusedGlobalSymbols
export const mutations: MutationTree<ShopState> = {
    init (state, payload: ShopInitPayload) {
        Object.assign(state, getDefaultState(), {
            search: payload.search,
            categorySlug: payload.categorySlug,
            options: payload.options,
            filters: payload.filters
        })
    },
    fetchProductsListStart (state) {
        state.categoryIsLoading = true
        state.productsListIsLoading = true
        state.query = buildQuery(state.options, state.filters)
    },
    fetchProductsListSuccess (state, payload: FetchProductsListSuccessPayload) {
        state.categoryIsLoading = false
        state.productsListIsLoading = false
        state.productsList = payload.productsList
    },
    fetchCategorySuccess (state, payload: FetchCategorySuccessPayload) {
        state.category = payload.category
    },
    fetchReceiptSuccess (state, payload: FetchReceiptSuccessPayload) {
        if (payload.receipt) {
            state.receipt = payload.receipt
        }
    },
    setOptionValue (state, payload: SetOptionValuePayload) {
        state.options.page = 1
        state.options[payload.option] = payload.value as any
    },
    setFilterValue (state, payload: SetFilterValuePayload) {
        if (payload.value === null) {
            Vue.delete(state.filters, payload.filter)
        } else {
            Vue.set(state.filters, payload.filter, payload.value)
        }

        state.options.page = 1
    },
    resetFilters (state) {
        state.filters = {}
        state.options.page = 1
    },
    setMerchant (state, payload: SetMerchantPayload) {
        state.merchant = payload.merchant
    }
}

let cancelPreviousCategoryRequest = () => {}
let cancelPreviousProductsListRequest = () => {}

// noinspection JSUnusedGlobalSymbols
export const actions: ActionTree<ShopState, {}> = {
    async init ({ dispatch, commit }, payload: ShopInitPayload): Promise<void> {
        commit('init', payload)
        await dispatch('fetchProductsList')
    },
    async fetchProductsList ({ commit, state }): Promise<void> {
        let canceled = false
        cancelPreviousProductsListRequest()
        cancelPreviousProductsListRequest = () => { canceled = true }
        commit('fetchProductsListStart')
        let { filters } = state
        if (state.categorySlug === null) {
            throw new Error('Invalid category')
        }
        filters = { ...filters, category: state.categorySlug }
        const results = await Promise.all([
            this.$shopApi.getProductsList(state.options, filters, state.search as string),
            this.$shopApi.getCategoryInfo(state.categorySlug),
        ])
        const productsList = results[0]
        const category = results[1]
        if (canceled && !process.server) {
            return
        }
        commit('fetchProductsListSuccess', { productsList })
        commit('fetchCategorySuccess', { category })
    },
    async fetchReceipt({ commit }, payload: FetchReceiptPayload): Promise<any> {
        const receiptData = await this.$shopApi.getReceipt(payload.uuid)
        commit('fetchReceiptSuccess', {})
        return receiptData
    },
    async setOptionValue ({ dispatch, commit }, payload: SetOptionValuePayload) {
        commit('setOptionValue', payload)

        await dispatch('fetchProductsList')
    },
    async setFilterValue ({ dispatch, commit }, payload: SetFilterValuePayload) {
        commit('setFilterValue', payload)

        await dispatch('fetchProductsList')
    },
    async resetFilters ({ dispatch, commit }) {
        commit('resetFilters')

        await dispatch('fetchProductsList')
    },
    async setMerchant ({ dispatch, commit }, payload: SetMerchantPayload) {
        commit('setMerchant', payload)
    }
}

// noinspection JSUnusedGlobalSymbols
export const getters: GetterTree<ShopState, {}> = {
    isLoading: (store) => {
        return store.categoryIsLoading || (store.productsListIsLoading && !store.productsList)
    },
    category: (store) => {
        return store.category
    },
    productsListIsLoading: (store) => {
        return store.productsListIsLoading
    },
    productsList (store) {
        return store.productsList
    },
    productsListFilters (store) {
        return store.productsList?.filters
    },
    options (store) {
        return store.options
    },
    filters (store) {
        return store.filters
    },
    query (store) {
        return store.query
    },
    merchant (store) {
        return store.merchant
    },
    search (store) {
        return store.search
    },
    receipt (store) {
        return store.receipt
    }
}
