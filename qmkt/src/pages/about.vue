<template>
    <div>
        <BlockAbout />
    </div>
</template>

<script lang="ts">

import { Vue, Component } from 'vue-property-decorator'
import { Context } from '@nuxt/types'
import BlockAbout from '~/components/blocks/block-about.vue'
import theme from '~/data/theme'

@Component({
    components: {
        BlockAbout,
    },
    async asyncData (context: Context) {
        context.store.dispatch('shop/setMerchant', { merchant: theme.merchant })
    },
    head () {
        return {
            title: 'About QMarket'
        }
    }
})
export default class AboutPage extends Vue {
}

</script>
