<template>
    <div :class="`product product--layout--${layout}`">
        <div class="product__content">
            <ProductGallery :layout="layout" :images="currentProduct.images" />

            <div class="product__info">
                <h1 class="product__name">
                    {{ currentProduct.name }}
                </h1>
                <!--<div class="product__rating">
                    <div class="product__rating-stars">
                        <Rating :value="currentProduct.rating" />
                    </div>
                    <div class="product__rating-legend">
                        <AppLink to="/">
                            {{ currentProduct.reviews }} Reviews
                        </AppLink>
                        <span>/</span>
                        <AppLink to="/">
                            Write A Review
                        </AppLink>
                    </div>
                </div>-->
                <div class="product__description" v-if="currentProduct.description">
                    <span v-html="currentProduct.description"></span>
                </div>
                <ul class="product__meta">
                    <li class="product__meta-availability" v-if="currentProduct.availability">
                        Availability:
                        <span class="text-success" v-if="currentProduct.availability == 'in-stock'">In Stock</span>
                        <template v-else>{{ currentProduct.availability }}</template>
                    </li>
                    <li v-if="currentProduct.brand">
                        Brand:
                        <template v-if="currentProduct.brand.url">
                            <AppLink :to="currentProduct.brand.url">
                                {{ currentProduct.brand.name }}
                            </AppLink>
                        </template>
                        <template v-else>
                            {{ currentProduct.brand.name }}
                        </template>
                    </li>
                    <li v-if="currentProduct.sku">SKU: {{ currentProduct.sku }}</li>
                </ul>
                <form v-if="product.variants.length > 1">
                    <div class="form-group product__option">
                        <!--suppress XmlInvalidId -->
                        <label for="product-quantity" class="product__option-label">Select</label>
                        <div>
                            <select name="productVariant" @change="selectVariant" v-model="variantIndex">
                                <option v-for="(pv, idx) in product.variants" :value="idx">{{ pv.name }}</option>
                            </select>
                         </div>
                    </div>
                </form>
            </div>

            <div class="product__sidebar">
                <div class="product__prices">
                    <template v-if="currentProduct.compareAtPrice">
                        <span class="product__new-price">
                            {{ $price(currentProduct.price) }}
                        </span>
                        <span class="product__old-price">
                            {{ $price(currentProduct.compareAtPrice) }}
                        </span>
                    </template>
                    <template v-if="!currentProduct.compareAtPrice">
                        {{ $price(currentProduct.price) }}
                    </template>
                </div>
                <!--<code>{{ currentProduct.attributes }}</code>-->
                <form class="product__options">
                    <div class="form-group product__option mb-3" v-for="attr in currentProduct.attributes" :key="attr.id">
                        <div class="product__option-label">
                            {{ attr.name }}
                        </div>
                        <div class="input-radio-label">
                            <div class="input-radio-label__list">
                                <label v-for="atv in attr.values" :key="atv.id">
                                    <input type="radio" :name="atv.slug" checked="checked" v-if="atv.active && attr.values.length > 1">
                                    <span>{{ atv.name }}</span>
                                </label>
                            </div>
                        </div>
                    </div>
                    <div class="form-group product__option">
                        <!--suppress XmlInvalidId -->
                        <label for="product-quantity" class="product__option-label">Quantity</label>
                        <div class="product__actions">
                            <div class="product__actions-item">
                                <InputNumber
                                    id="product-quantity"
                                    v-model="quantity"
                                    aria-label="Quantity"
                                    class="product__quantity"
                                    size="lg"
                                    :min="1"
                                />
                            </div>
                            <div class="product__actions-item product__actions-item--addtocart">
                                <AsyncAction v-slot="{ run, isLoading }" :action="addToCart">
                                    <button
                                        type="button"
                                        :class="[
                                            'btn btn-primary btn-lg',
                                            {'btn-loading': isLoading}
                                        ]"
                                        :disabled="!quantity"
                                        @click="run"
                                    >
                                        Add to cart
                                    </button>
                                </AsyncAction>
                            </div>
                        </div>
                    </div>
                </form>
            </div>

            <!--<div class="product__footer">
                <div class="product__tags tags">
                    <div class="tags__list">
                        <AppLink to="/">
                            Mounts
                        </AppLink>
                        <AppLink to="/">
                            Electrodes
                        </AppLink>
                        <AppLink to="/">
                            Chainsaws
                        </AppLink>
                    </div>
                </div>-->

                <!--<div class="product__share-links share-links">
                    <ul class="share-links__list">
                        <li class="share-links__item share-links__item--type--like">
                            <AppLink to="/">
                                Like
                            </AppLink>
                        </li>
                        <li class="share-links__item share-links__item--type--tweet">
                            <AppLink to="/">
                                Tweet
                            </AppLink>
                        </li>
                        <li class="share-links__item share-links__item--type--pin">
                            <AppLink to="/">
                                Pin It
                            </AppLink>
                        </li>
                        <li class="share-links__item share-links__item--type--counter">
                            <AppLink to="/">
                                4K
                            </AppLink>
                        </li>
                    </ul>
                </div>-->
            </div>
        </div>
    </div>
</template>

<script lang="ts">
import { Vue, Component, Prop, Inject } from 'vue-property-decorator'
import { IProduct, IProductAttribute, IProductAttributeValue, IProductAttributeSelect } from '~/interfaces/product'
import Rating from '~/components/shared/rating.vue'
import ProductGallery from '~/components/shared/product-gallery.vue'
import AppLink from '~/components/shared/app-link.vue'
import AsyncAction from '~/components/shared/async-action.vue'
import InputNumber from '~/components/shared/input-number.vue'
import Wishlist16Svg from '~/svg/wishlist-16.svg'
import Compare16Svg from '~/svg/compare-16.svg'
import { getProductUriByAttributes } from '~/api/catalog'

export type ProductLayout = 'standard' | 'sidebar' | 'columnar' | 'quickview';

@Component({
    components: { Rating, AppLink, ProductGallery, AsyncAction, Wishlist16Svg, Compare16Svg, InputNumber }
})
export default class Product extends Vue {
    @Prop({ type: String, required: true }) readonly layout!: ProductLayout
    @Prop({ type: Object, required: true }) readonly product!: IProduct

    quantity: number | string = 1
    variantIndex: number = this.product.selected as number
    currentProduct: IProduct = (this.product.variants.length > 0) ? this.product.variants[this.product.selected as number] : this.product

    selectVariant (input: any) {
        this.currentProduct = this.product.variants[this.variantIndex]
    }

    /*async selectAttribute (attr: IProductAttribute, atv: IProductAttributeValue) {
        if (atv.active) {
            return
        }
        // TODO: fix
        const gs = await this.$shopApi.getMerchantProduct(this.$route.params.merchant_id)
        const res = await getProductUriByAttributes(gs.graph, this.currentProduct.attributes, {
            attributeUri: attr.uri,
            valueUri: atv.uri,
        })
        if (res) {
            for (var i = 0; i < this.product.variants.length; i++) {
                if (this.product.variants[i].uri === res) {
                    this.variantIndex = i
                    this.currentProduct = this.product.variants[i]
                    break
                }
            }
        }
    }*/

    addToCart (): Promise<void> {
        if (typeof this.quantity === 'string' || this.quantity < 1) {
            return Promise.resolve()
        }
        return this.$store.dispatch('cart/add', { product: this.currentProduct, quantity: this.quantity })
    }
}
</script>
