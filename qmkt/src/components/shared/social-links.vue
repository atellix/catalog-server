<template>
    <div :class="[$attrs.class, 'social-links', `social-links--shape--${shape}`]">
        <ul class="social-links__list">
            <li v-for="item in items" :key="item.type" class="social-links__item">
                <a
                    :class="['social-links__link', `social-links__link--type--${item.type}`]"
                    :href="item.url"
                    target="_blank"
                >
                    <i :class="item.icon" />
                </a>
            </li>
        </ul>
    </div>
</template>

<script lang="ts">
import { Vue, Component, Prop } from 'vue-property-decorator'
import { IMerchant } from '~/interfaces/merchant'
import theme from '~/data/theme'

const socialNetworkDetector = require('social-network-detector')

type Shape = 'circle' | 'rounded';

@Component
export default class SocialLinks extends Vue {
    @Prop({ type: String, default: () => 'circle' }) readonly shape!: Shape
    @Prop({ type: Object, required: true }) readonly merchant!: IMerchant

    get items() {
        const socialNets = [
            ['youtube', 'fab fa-youtube'],
            ['instagram', 'fab fa-instagram'],
            ['facebook', 'fab fa-facebook-f'],
            ['twitter', 'fab fa-twitter'],
            ['linkedin', 'fab fa-linkedin'],
            ['telegram', 'fab fa-telegram'],
            ['whatsapp', 'fab fa-whatsapp'],
            ['github', 'fab fa-github'],
            ['spotify', 'fab fa-spotify'],
            ['medium', 'fab fa-medium'],
            ['pinterest', 'fab fa-pinterest'],
        ]
        var itemlist = []
        var found: { [key: string]: any } = {}
        for (var j = 0; j < this.merchant.links.length; j++) {
            const link = this.merchant.links[j]
            const dt = socialNetworkDetector.detect(link)
            if (dt) {
                found[dt] = link
            }
        }
        for (var i = 0; i < socialNets.length; i++) {
            const sn = socialNets[i]
            if (sn[0] in found) {
                itemlist.push({
                    type: sn[0],
                    icon: sn[1],
                    url: found[sn[0]],
                })
            }
        }
        return itemlist
    }
}
</script>
