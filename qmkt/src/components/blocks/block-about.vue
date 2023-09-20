<template>
    <div class="block block-banner">
        <div class="container">
            <p class="mt-5"><strong>About QMarket</strong></p>
            <p class="mt-2">Welcome to QMarket.club!</p>
            <p class="mt-3">QMarket is powered by the <a href="https://atellix.com/">Atellix Commerce Engine</a>.</p>
            <p class="mt-2">The future of e-commerce is at your fingertips, without the complexity of coding. Seamlessly join our thriving ecosystem with utmost simplicity and affordability. We believe growth should be accessible to all merchants, and that's why our platform breaks down entry barriers.</p>
            <p class="mt-2">Imagine your products effortlessly taking center stage across a multitude of websites. Streamline your revenue flow with integrated credit card support. No more friction or interruptions – just seamless transactions that allow you to concentrate on expanding your business horizons.</p>
            <p class="mt-2">The bridge between your virtual success and real-world utility is fortified through strategic partnerships. Our network allows merchants to channel their revenue through established exchanges like <a href="https://coinbase.com/">Coinbase</a>, facilitating smooth conversion to traditional banking systems.</p>
            <p class="mt-2">Through <a href="https://atellix.com/">Atellix Commerce Engine</a>, we provide dynamic product discovery network to make product marketing a breeze.</p>
            <p class="mt-2">Bid farewell to coding complexities and let your offerings shine on our vibrant marketplace.</p>
            <div class="mt-2">
                <a href="https://app.atellix.com/app/login" class="block-banner__body">
                    <div class="block-banner__button">
                        <span class="btn btn-sm btn-primary">Merchant Sign Up &raquo;</span>
                    </div>
                </a>
            </div>
        </div>
    </div>
</template>

<script lang="ts">

import { Vue, Component } from 'vue-property-decorator'
import AppLink from '~/components/shared/app-link.vue'

@Component({
    components: { AppLink }
})
export default class BlockAbout extends Vue { }

</script>
