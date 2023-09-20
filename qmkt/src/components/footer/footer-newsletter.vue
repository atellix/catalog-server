<template>
    <div class="site-footer__widget footer-newsletter">
        <h5 class="footer-newsletter__title">
            Social
        </h5>

        <social-links class="footer-newsletter__social-links" shape="circle" :merchant="merchant"/>
    </div>
</template>

<script lang="ts">

import { Vue, Component, Prop } from 'vue-property-decorator'
import { IMerchant } from '~/interfaces/merchant'
import SocialLinks from '~/components/shared/social-links.vue'

@Component({
    components: { SocialLinks }
})
export default class FooterNewsletter extends Vue {
    @Prop({ type: Object, required: true }) readonly merchant!: IMerchant
}

</script>
