<template>
    <ShopPageProduct :product="product" layout="standard" />
</template>
<script lang="ts">
import { Vue, Component } from 'vue-property-decorator'
import { Context } from '@nuxt/types'
import { IProduct } from '~/interfaces/product'
import { IMerchant } from '~/interfaces/merchant'
import ShopPageProduct from '~/components/shop/shop-page-product.vue'

@Component({
    components: { ShopPageProduct },
    async asyncData (context: Context): Promise<{ product: IProduct }> {
        const info = await context.$shopApi.getMerchantProduct(context.route.params.product_key)
        context.store.dispatch('shop/setMerchant', { merchant: info.merchant })
        return { product: info.product }
    }
})
export default class Page extends Vue {
    product: IProduct = null!
}
</script>
