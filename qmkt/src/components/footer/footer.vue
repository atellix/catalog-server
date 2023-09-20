<template>
    <div class="site-footer">
        <div class="container">
            <div class="site-footer__widgets">
                <div class="row">
                    <div class="col-12 col-md-6 col-lg-4">
                        <footer-contacts :merchant="merchant"/>
                    </div>
                    <div class="col-12 col-md-6 col-lg-4">
                        <footer-links
                            title="Resources"
                            :links="[
                                {title: merchant.name, url: merchant.url},
                                {title: 'About QMarket', url: '/about'},
                            ]"
                        />
                    </div>
                    <div class="col-12 col-md-12 col-lg-4">
                        <footer-newsletter :merchant="merchant" />
                    </div>
                </div>
            </div>

            <div class="site-footer__bottom">
                <div class="site-footer__copyright">
                    <!-- copyright -->
                    Powered by <img style="height: 12px;" :src="$url.img('/images/solana-logo2x.png')" alt=""/> - 
                    <AppLink to="/about">About QMarket</AppLink>
                    |
                    <a href="https://atellix.com/" target="_blank">Atellix Network</a>
                    |
                    <a href="https://atellix.com/terms.html" target="_blank">Terms of Service</a>
                    <!--|
                    <a href="#" target="_blank">Privacy Policy</a>-->
                    <!-- copyright / end -->
                </div>
                <div class="site-footer__payments">
                    <!--<img :src="$url.img('/images/payments.png')" alt="">-->
                </div>
            </div>
        </div>
        <ToTop />
    </div>
</template>

<script lang="ts">

import { Vue, Component, Prop } from 'vue-property-decorator'
import { IMerchant } from '~/interfaces/merchant'
import FooterContacts from '~/components/footer/footer-contacts.vue'
import FooterLinks from '~/components/footer/footer-links.vue'
import FooterNewsletter from '~/components/footer/footer-newsletter.vue'
import ToTop from '~/components/footer/to-top.vue'

@Component({
    components: { ToTop, FooterNewsletter, FooterLinks, FooterContacts }
})

export default class Footer extends Vue {
    @Prop({ type: Object, required: true }) readonly merchant!: IMerchant
}

</script>
