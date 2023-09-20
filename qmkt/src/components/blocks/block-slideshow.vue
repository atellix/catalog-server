<template>
    <!-- .block-slideshow -->
    <div
        :class="[
            'block-slideshow',
            `block-slideshow--layout--${layout}`,
            'block'
        ]"
    >
        <div class="container">
            <div class="row">
                <div v-if="layout === 'with-departments'" class="col-lg-3 d-none d-lg-block" />
                <div
                    :class="[
                        'col-12',
                        {'col-lg-9': layout === 'with-departments'}
                    ]"
                >
                    <div class="block-slideshow__body">
                        <Carousel>
                            <CarouselSlide v-for="(slide, index) in slides" :key="index">
                                <AppLink class="block-slideshow__slide" to="/">
                                    <div
                                        class="block-slideshow__slide-image block-slideshow__slide-image--desktop"
                                        :style="{ backgroundImage: getDesktopImage(slide) }"
                                    />
                                    <div
                                        class="block-slideshow__slide-image block-slideshow__slide-image--mobile"
                                        :style="{ backgroundImage: getMobileImage(slide) }"
                                    />
                                    <div class="block-slideshow__slide-content">
                                        <!-- eslint-disable-next-line vue/no-v-html -->
                                        <div class="block-slideshow__slide-title" v-html="slide.title" />
                                        <!-- eslint-disable-next-line vue/no-v-html -->
                                        <div class="block-slideshow__slide-text" v-html="slide.text" />
                                        <div class="block-slideshow__slide-button">
                                            <AppLink to="/about"><span class="btn btn-primary btn-lg">About QMarket</span></AppLink>
                                        </div>
                                    </div>
                                </AppLink>
                            </CarouselSlide>
                        </Carousel>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <!-- .block-slideshow / end -->
</template>

<script lang="ts">

import { Vue, Component, Prop } from 'vue-property-decorator'
import { Getter } from 'vuex-class'
import { ILanguage } from '~/interfaces/language'
import departments from '~/services/departments'
import Carousel from '~/components/shared/carousel.vue'
import CarouselSlide from '~/components/shared/carousel-slide.vue'
import AppLink from '~/components/shared/app-link.vue'

type BlockSlideshowLayout = 'full' | 'with-departments';

interface SlideImage {
    ltr: string
    rtl: string
}

interface Slide {
    title: string
    text: string
    imageClassic: SlideImage
    imageFull: SlideImage
    imageMobile: SlideImage
}

@Component({
    components: { CarouselSlide, Carousel, AppLink }
})
export default class BlockSlideshow extends Vue {
    @Prop({ type: String, default: () => 'full' }) readonly layout!: BlockSlideshowLayout
    @Getter('locale/language') language!: ILanguage

    slides: Slide[] = [
        {
            title: '<div style="background-color: rgba(255, 255, 255, .75); padding: 10px; border-radius: 10px;"><span class="logo-font" style="font-size: 28px;">Welcome To QMarket</span></div>',
            text: '<div style="background-color: rgba(255, 255, 255, .75); padding: 10px; border-radius: 10px;"><span class="logo-font" style="font-size: 20px;">Products & Services<br/>Marketplace</span></div>',
            imageClassic: {
                ltr: '/images/slides/slide-1-ltr.jpg',
                rtl: '/images/slides/slide-1-rtl.jpg'
            },
            imageFull: {
                ltr: '/images/slides/slide-1-full-ltr.jpg',
                rtl: '/images/slides/slide-1-full-rtl.jpg'
            },
            imageMobile: {
                ltr: '/images/slides/slide-1-mobile.jpg',
                rtl: '/images/slides/slide-1-mobile.jpg'
            }
        },
        {
            title: '<div style="background-color: rgba(255, 255, 255, .75); padding: 10px; border-radius: 10px;"><span class="logo-font" style="font-size: 28px;">Effortless For Merchants</span></div>',
            text: '<div style="background-color: rgba(255, 255, 255, .75); padding: 10px; border-radius: 10px;"><span class="logo-font" style="font-size: 20px;">Streamlined Setup Ensures You Quickly<br/>Start Selling Your Products</span></div>',
            imageClassic: {
                ltr: '/images/slides/slide-2-ltr.jpg',
                rtl: '/images/slides/slide-2-rtl.jpg'
            },
            imageFull: {
                ltr: '/images/slides/slide-2-full-ltr.jpg',
                rtl: '/images/slides/slide-2-full-rtl.jpg'
            },
            imageMobile: {
                ltr: '/images/slides/slide-2-mobile.jpg',
                rtl: '/images/slides/slide-2-mobile.jpg'
            }
        },
        {
            title: '<div style="background-color: rgba(255, 255, 255, .75); padding: 10px; border-radius: 10px;"><span class="logo-font" style="font-size: 28px;">Powered By Solana</span></div>',
            text: '<div style="background-color: rgba(255, 255, 255, .75); padding: 10px; border-radius: 10px;"><span class="logo-font" style="font-size: 20px;">Cost-Effective &<br/>User-Friendly Solution<br/>For Merchants of All Kinds</span></div>',
            imageClassic: {
                ltr: '/images/slides/slide-3-ltr.jpg',
                rtl: '/images/slides/slide-3-rtl.jpg'
            },
            imageFull: {
                ltr: '/images/slides/slide-3-full-ltr.jpg',
                rtl: '/images/slides/slide-3-full-rtl.jpg'
            },
            imageMobile: {
                ltr: '/images/slides/slide-3-mobile.jpg',
                rtl: '/images/slides/slide-3-mobile.jpg'
            }
        }
    ]

    get direction () {
        return this.language.direction
    }

    mounted () {
        departments.set(this.$el)
    }

    beforeDestroy () {
        departments.set(null)
    }

    getDesktopImage (slide: Slide): string {
        const url = (this.layout === 'with-departments' ? slide.imageClassic : slide.imageFull)[this.direction]

        return `url(${this.$url.img(url)})`
    }

    getMobileImage (slide: Slide): string {
        return `url(${this.$url.img(slide.imageMobile[this.direction])})`
    }
}

</script>
