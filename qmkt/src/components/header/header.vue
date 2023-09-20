<template>
    <div class="site-header">
        <Topbar :merchant="merchant"/>

        <div v-if="layout === 'default'" class="site-header__middle container">
            <div class="site-header__logo">
                <AppLink to="/">
                    <!-- logo -->
                    <div class="logo-font">QMarket</div>
                    <!-- logo / end -->
                </AppLink>
            </div>
            <div class="site-header__search">
                <Search location="header" />
            </div>
            <div v-if="merchant.phone" class="site-header__phone">
                <div class="site-header__phone-title">
                    {{ merchant.name }}
                </div>
                <div class="site-header__phone-number">
                    {{ merchant.phone }}
                </div>
            </div>
        </div>

        <div class="site-header__nav-panel">
            <NavPanel :layout="layout" sticky-mode="alwaysOnTop" />
        </div>
    </div>
</template>

<script lang="ts">

import { Vue, Component, Prop } from 'vue-property-decorator'
import { State } from 'vuex-class'
import { RootState } from '~/store'
import { HeaderLayout } from '~/store/options'
import { IMerchant } from '~/interfaces/merchant'
import Search from '~/components/header/search.vue'
import NavPanel from '~/components/header/nav-panel.vue'
import Topbar from '~/components/header/topbar.vue'
import AppLink from '~/components/shared/app-link.vue'

@Component({
    components: { AppLink, NavPanel, Search, Topbar }
})
export default class Header extends Vue {
    @Prop({ type: Object, required: true }) readonly merchant!: IMerchant

    @State((state: RootState) => state.options.headerLayout) layout!: HeaderLayout
}

</script>
