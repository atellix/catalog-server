<template>
    <div class="typography">
        <h3>Description</h3>
        <p><span v-html="product.description"></span></p>
    </div>
</template>

<script lang="ts">

import { Vue, Prop, Component } from 'vue-property-decorator'
import { IProduct } from '~/interfaces/product'

@Component
export default class ProductTabDescription extends Vue {
    @Prop({ type: Object, required: true }) readonly product!: IProduct
}

</script>
