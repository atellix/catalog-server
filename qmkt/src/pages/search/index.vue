<template>
    <ShopPageSearch />
</template>

<script lang="ts">

import { Context } from '@nuxt/types'
import { Vue, Watch, Component } from 'vue-property-decorator'
import { ParsedQuery } from 'query-string'
import { parseQueryFilters, parseQueryOptions } from '~/services/helpers'
import ShopPageSearch from '~/components/shop/shop-page-search.vue'
import theme from '~/data/theme'

async function searchQuery (context: Context) {
    const query = context.query
    const options = parseQueryOptions(query as ParsedQuery)
    const filters = parseQueryFilters(query as ParsedQuery)
    await context.store.dispatch('shop/init', {
        search: query.q,
        categorySlug: null,
        options,
        filters
    })
}

@Component({
    components: { ShopPageSearch },
    async asyncData (context): Promise<object | void> {
        await searchQuery(context)
        context.store.dispatch('shop/setMerchant', { merchant: theme.merchant })
    }
})
export default class Page extends Vue {
    init: boolean = true
    @Watch('$route', { immediate: true, deep: true })
    onUrlChange(newVal: any) {
        if (this.init) {
            this.init = false
            return
        }
        searchQuery(this.$nuxt.context).then()
    }
}

</script>
