<template>
    <div>
        <PageHeader :breadcrumb="breadcrumb" />

        <div v-if="layout === 'sidebar'" class="container">
            <div :class="`shop-layout shop-layout--sidebar--${sidebarPosition}`">
                <ProductSidebar v-if="sidebarPosition === 'start'" class="shop-layout__sidebar" />

                <div class="shop-layout__content">
                    <div class="block">
                        <Product :product="product" :layout="layout" />
                        <ProductTabs :with-sidebar="true" />
                    </div>

                    <BlockProductsCarousel
                        v-if="relatedProducts.length > 0"
                        title="Related Products"
                        layout="grid-4-sm"
                        :products="relatedProducts"
                        :with-sidebar="true"
                    />
                </div>

                <ProductSidebar v-if="sidebarPosition === 'end'" class="shop-layout__sidebar" />
            </div>
        </div>

        <template v-if="layout !== 'sidebar'">
            <div class="block mt-3">
                <div class="container">
                    <Product :product="product" :layout="layout" @selectVariant="selectVariant"/>
                    <ProductTabs :product="currentProduct"/>
                </div>
            </div>
        </template>
    </div>
</template>

<script lang="ts">

import { Vue, Component, Prop } from 'vue-property-decorator'
import { IProduct } from '~/interfaces/product'
import { ILink } from '~/interfaces/menus/link'
import PageHeader from '~/components/shared/page-header.vue'
import Product from '~/components/shared/product.vue'
import BlockProductsCarousel from '~/components/blocks/block-products-carousel.vue'
import ProductTabs from '~/components/shop/product-tabs.vue'
import ProductSidebar from '~/components/shop/product-sidebar.vue'

export type ShopPageProductLayout = 'standard' | 'sidebar' | 'columnar';
export type ShopPageProductSidebarPosition = 'start' | 'end';

@Component({
    components: { PageHeader, Product, ProductTabs, BlockProductsCarousel, ProductSidebar },
    head (this: ShopPageProduct) {
        return {
            title: `${this.product.name}`
        }
    }
})
export default class ShopPageProduct extends Vue {
    @Prop({ type: Object, required: true }) readonly product!: IProduct
    @Prop({ type: String, default: () => 'standard' }) readonly layout!: ShopPageProductLayout
    @Prop({ type: String, default: () => 'start' }) readonly sidebarPosition!: ShopPageProductSidebarPosition

    relatedProducts: IProduct[] = []
    currentProduct: IProduct = this.product

    get breadcrumb (): ILink[] {
        var base: ILink[] = [
            { title: 'Home', url: this.$url.home() },
        ]
        base = base.concat(this.product.categoryPath)
        base = base.concat({ title: this.product.name, url: this.$url.product(this.product) })
        return base
    }

    selectVariant (newProduct: IProduct): void {
        this.currentProduct = newProduct
    }

    //mounted () {}
}

</script>
