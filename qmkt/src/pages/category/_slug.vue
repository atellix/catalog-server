<template>
    <ShopPageCategory />
</template>

<script lang="ts">

import { Vue, Component } from 'vue-property-decorator'
import { ParsedQuery } from 'query-string'
import { parseQueryFilters, parseQueryOptions } from '~/services/helpers'
import ShopPageCategory from '~/components/shop/shop-page-category.vue'
import theme from '~/data/theme'

@Component({
    components: { ShopPageCategory },
    async asyncData ({ store, params, query }): Promise<object | void> {
        const options = parseQueryOptions(query as ParsedQuery)
        const filters = parseQueryFilters(query as ParsedQuery)
        await store.dispatch('shop/init', {
            //merchantId: params.merchant_id,
            categorySlug: params.slug || null,
            options,
            filters
        })
        store.dispatch('shop/setMerchant', { merchant: theme.merchant })
    }
})
export default class Page extends Vue { }

</script>
