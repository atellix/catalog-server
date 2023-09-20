<template>
    <!-- .topbar -->
    <div class="site-header__topbar topbar">
        <div class="topbar__container container">
            <div class="topbar__row">
                <div class="topbar__item topbar__item--link">
                    <AppLink to="/about" class="topbar-link">
                        About QMarket
                    </AppLink>
                </div>
                <div class="topbar__spring" />
                <div class="topbar__item topbar__item--link">
                    <AppLink to="https://atellix.network/" class="topbar-link">
                        Atellix Network
                    </AppLink>
                </div>
            </div>
        </div>
    </div>
    <!-- .topbar / end -->
</template>

<script lang="ts">

import { Vue, Component, Prop } from 'vue-property-decorator'
import { Getter, Mutation, State } from 'vuex-class'
import { RootState } from '~/store'
import { ICurrency } from '~/interfaces/currency'
import { ILanguage } from '~/interfaces/language'
import { IMerchant } from '~/interfaces/merchant'
import Dropdown from '~/components/header/dropdown.vue'
import AppLink from '~/components/shared/app-link.vue'
import dataLanguages from '~/data/languages'
import dataShopCurrencies from '~/data/shopCurrencies'

@Component({
    components: { Dropdown, AppLink }
})
export default class Topbar extends Vue {
    @State((state: RootState) => state.currency.current) currency!: ICurrency
    @Getter('locale/language') language!: ILanguage
    @Mutation('currency/set') setCurrency!: (currency: ICurrency) => void
    @Prop({ type: Object, required: true }) readonly merchant!: IMerchant

    currencies = dataShopCurrencies.map((currency) => {
        return {
            title: `${currency.symbol} ${currency.name}`,
            currency
        }
    })

    languages = dataLanguages.map((language) => {
        return {
            title: language.name,
            icon: language.icon,
            locale: language.locale
        }
    })

    setLanguage (locale: string) {
        const fullPath = this.$route.fullPath
        const re = new RegExp('^/(' + dataLanguages.map(x => x.locale).join('|') + ')(/|$)')
        const path = fullPath.replace(re, '/')

        this.$router.push(`/${locale}${path}`)
    }
}

</script>
