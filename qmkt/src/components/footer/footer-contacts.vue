<template>
    <div class="site-footer__widget footer-contacts">
        <h5 class="footer-contacts__title">
            {{ merchant.name }}
        </h5>

        <!--<div class="footer-contacts__text">
            Details:
        </div>-->

        <ul class="footer-contacts__contacts text-left ml-1">
            <li v-if="merchant.email">
                <i class="footer-contacts__icon far fa-envelope" />
                {{ merchant.email }}
            </li>
            <li v-if="merchant.phone">
                <i class="footer-contacts__icon fas fa-mobile-alt" />
                {{ merchant.phone }}
            </li>
            <li v-if="merchant.hours">
                <i class="footer-contacts__icon far fa-clock" />
                {{ merchant.hours }}
            </li>
            <li>
                <div class="float-left mr-1"><i class="footer-contacts__icon fas fa-globe-americas" /></div>
                <div class="float-left">
                    <template v-if="merchant.address">{{ merchant.address }}<br/></template>
                    <template v-if="merchant.city && merchant.region && merchant.postalCode">{{ merchant.city }},
                    {{ merchant.region }}
                    {{ merchant.postalCode }}<br/></template>
                    <template v-else-if="merchant.region">{{ merchant.region }}</template>
                    <template v-if="merchant.country">{{ merchant.country }}</template>
                </div>
                <br clear="all"/>
            </li>
        </ul>
    </div>
</template>

<script lang="ts">

import { Vue, Component, Prop } from 'vue-property-decorator'
import { IMerchant } from '~/interfaces/merchant'

@Component
export default class FooterContacts extends Vue {
    @Prop({ type: Object, required: true }) readonly merchant!: IMerchant
}

</script>
