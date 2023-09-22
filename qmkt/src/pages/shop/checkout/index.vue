<template>
    <div>
        <client-only>
            <PageHeader
                title="Checkout"
                :breadcrumb="[
                    { title: 'Home', url: $url.home() },
                    { title: 'Shopping Cart', url: $url.cart() },
                    { title: 'Checkout', url: '' },
                ]"
            />
            <div class="checkout block">
                <div class="container">
                    <div class="row">
                        <!--<div class="col-12 mb-3">
                            <div class="alert alert-primary alert-lg">
                                Returning customer?
                                <AppLink :to="$url.signIn()">
                                    Click here to login
                                </AppLink>
                            </div>
                        </div>-->
                        <div class="col-12 col-lg-6 col-xl-7">
                            <div class="card mb-lg-0">
                                <div class="card-body">
                                    <h3 class="card-title">
                                        Billing Details
                                    </h3>
                                    <div class="form-row">
                                        <div class="form-group col-md-6">
                                            <label for="checkout-first-name">First Name</label>
                                            <input
                                                v-model="billingAddress.firstName"
                                                id="checkout-first-name"
                                                class="form-control"
                                                :class="(billingAddressError['firstName']) ? ['is-invalid'] : []"
                                                type="text"
                                                placeholder="First name"
                                            >
                                        </div>
                                        <div class="form-group col-md-6">
                                            <label for="checkout-last-name">Last Name</label>
                                            <input
                                                v-model="billingAddress.lastName"
                                                id="checkout-last-name"
                                                class="form-control"
                                                :class="(billingAddressError['lastName']) ? ['is-invalid'] : []"
                                                type="text"
                                                placeholder="Last name"
                                            >
                                        </div>
                                    </div>
                                    <div class="form-row">
                                        <div class="form-group col-md-6">
                                            <label for="checkout-company-name">
                                                Company
                                                <span class="text-muted">(Optional)</span>
                                            </label>
                                            <input
                                                v-model="billingAddress.company"
                                                id="checkout-company-name"
                                                class="form-control"
                                                :class="(billingAddressError['company']) ? ['is-invalid'] : []"
                                                type="text"
                                                placeholder="Company"
                                            >
                                        </div>
                                    </div>
                                    <hr/>
                                    <div class="form-row">
                                        <div class="form-group col-md-6">
                                            <label for="checkout-email">Email</label>
                                            <input
                                                v-model="billingAddress.email"
                                                id="checkout-email"
                                                class="form-control"
                                                :class="(billingAddressError['email']) ? ['is-invalid'] : []"
                                                type="email"
                                                placeholder="Email"
                                            >
                                        </div>
                                        <div class="form-group col-md-6">
                                            <label for="checkout-phone">
                                                Phone
                                                <span class="text-muted">(Optional)</span>
                                            </label>
                                            <masked-input
                                                pattern="(111) 111-1111"
                                                v-model="billingAddress.phone"
                                                id="checkout-phone"
                                                class="form-control"
                                                :class="(billingAddressError['phone']) ? ['is-invalid'] : []"
                                                type="text"
                                            ></masked-input>
                                        </div>
                                    </div>
                                    <hr/>
                                    <div class="form-row">
                                        <div class="form-group col-md-6">
                                            <label for="checkout-street-address">Address</label>
                                            <input
                                                v-model="billingAddress.address"
                                                id="checkout-street-address"
                                                class="form-control"
                                                :class="(billingAddressError['address']) ? ['is-invalid'] : []"
                                                type="text"
                                                placeholder="Address"
                                            >
                                        </div>
                                        <div class="form-group col-md-6">
                                            <label for="checkout-address2">
                                                Apt./Ste./Unit#
                                                <span class="text-muted">(Optional)</span>
                                            </label>
                                            <input
                                                v-model="billingAddress.address2"
                                                id="checkout-address2"
                                                class="form-control"
                                                :class="(billingAddressError['address2']) ? ['is-invalid'] : []"
                                                type="text"
                                                placeholder="Apartment, suite, or unit #"
                                            >
                                        </div>
                                    </div>
                                    <div class="form-row">
                                        <div class="form-group col-md-6">
                                            <label for="checkout-city">City</label>
                                            <input
                                                v-model="billingAddress.city"
                                                id="checkout-city"
                                                class="form-control"
                                                :class="(billingAddressError['city']) ? ['is-invalid'] : []"
                                                type="text"
                                                placeholder="City"
                                            >
                                        </div>
                                        <div class="form-group col-md-6">
                                            <label for="checkout-region">State</label>
                                            <select
                                                v-model="billingAddress.region"
                                                id="checkout-region"
                                                class="form-control"
                                                :class="(billingAddressError['region']) ? ['is-invalid'] : []"
                                            >
                                                <option value="">Select State</option>
                                                <option v-for="st in usStatesList" :key="st[0]" :value="st[0]">{{ st[1] }}</option>
                                            </select>
                                        </div>
                                    </div>
                                    <div class="form-row">
                                        <div class="form-group col-md-6">
                                            <label for="checkout-postcode">Zipcode</label>
                                            <input
                                                v-model="billingAddress.postcode"
                                                id="checkout-postcode"
                                                class="form-control"
                                                :class="(billingAddressError['postcode']) ? ['is-invalid'] : []"
                                                type="text"
                                                placeholder="Zipcode"
                                                maxlength="5"
                                            >
                                        </div>
                                    </div>
                                    <!--<div class="form-group">
                                        <label for="checkout-country">Country</label>
                                        <select v-model="billingAddress.country" id="checkout-country" class="form-control">
                                            <option value="">Select a country...</option>
                                            <option value="us">United States</option>
                                        </select>
                                    </div>-->
                                    <!--<div class="form-group">
                                        <div class="form-check">

                                            <span class="form-check-input input-check">
                                                <span class="input-check__body">
                                                    <input
                                                        id="checkout-create-account"
                                                        class="input-check__input"
                                                        type="checkbox"
                                                    >
                                                    <span class="input-check__box" />
                                                    <Check9x7Svg class="input-check__icon" />
                                                </span>
                                            </span>
                                            <label class="form-check-label" for="checkout-create-account">
                                                Create an account?
                                            </label>
                                        </div>
                                    </div>-->
                                </div>
                                <div class="card-divider" />
                                <div class="card-body">
                                    <h3 class="card-title">
                                        Shipping Details
                                    </h3>
                                    <div class="form-group">
                                        <div class="form-check">
                                            <span class="form-check-input input-check">
                                                <span class="input-check__body">
                                                    <input
                                                        v-model="sameAddress"
                                                        id="checkout-same-address"
                                                        class="input-check__input"
                                                        type="checkbox"
                                                    >
                                                    <span class="input-check__box" />
                                                    <Check9x7Svg class="input-check__icon" />
                                                </span>
                                            </span>
                                            <label class="form-check-label" for="checkout-same-address">
                                                Ship to same address?
                                            </label>
                                        </div>
                                    </div>
                                    <template v-if="!sameAddress">
                                        <h4>Shipping Address</h4>
                                        <div class="form-row">
                                            <div class="form-group col-md-6">
                                                <label for="checkout-street-address">Address</label>
                                                <input
                                                    v-model="shippingAddress.address"
                                                    id="checkout-street-address"
                                                    class="form-control"
                                                    type="text"
                                                    placeholder="Address"
                                                >
                                            </div>
                                            <div class="form-group col-md-6">
                                                <label for="checkout-address">
                                                    Apt./Ste./Unit#
                                                    <span class="text-muted">(Optional)</span>
                                                </label>
                                                <input
                                                    v-model="shippingAddress.address2"
                                                    id="checkout-address"
                                                    class="form-control"
                                                    type="text"
                                                    placeholder="Apartment, suite, or unit #"
                                                >
                                            </div>
                                        </div>
                                        <div class="form-row">
                                            <div class="form-group col-md-6">
                                                <label for="checkout-city">City</label>
                                                <input
                                                    v-model="shippingAddress.city"
                                                    id="checkout-city"
                                                    class="form-control"
                                                    type="text"
                                                    placeholder="City"
                                                >
                                            </div>
                                            <div class="form-group col-md-6">
                                                <label for="checkout-state">State</label>
                                                <input
                                                    v-model="shippingAddress.region"
                                                    id="checkout-state"
                                                    class="form-control"
                                                    type="text"
                                                >
                                            </div>
                                        </div>
                                        <div class="form-row">
                                            <div class="form-group col-md-6">
                                                <label for="checkout-postcode">Zipcode</label>
                                                <input
                                                    v-model="shippingAddress.postcode"
                                                    id="checkout-postcode"
                                                    class="form-control"
                                                    type="text"
                                                    placeholder="Zipcode"
                                                >
                                            </div>
                                        </div>
                                    </template>
                                    <!--<div class="form-group">
                                        <label for="checkout-comment">
                                            Delivery notes
                                            <span class="text-muted">(Optional)</span>
                                        </label>
                                        <textarea id="checkout-comment" class="form-control" :rows="4" />
                                    </div>-->
                                </div>
                            </div>
                        </div>
                        <div class="col-12 col-lg-6 col-xl-5 mt-4 mt-lg-0">
                            <div class="card mb-0">
                                <div class="card-body">
                                    <h3 class="card-title">
                                        Your Order
                                    </h3>
                                    <template v-if="$store.state.cart.merchants.length > 1">
                                        <div v-for="mrch in $store.state.cart.merchants" :key="mrch.id">
                                            <div class="text-center" style="font-size: 1.25em;">{{ mrch.label }}</div>
                                            <table class="checkout__totals">
                                                <thead class="checkout__totals-header">
                                                    <tr>
                                                        <th>Product</th>
                                                        <th>Total</th>
                                                    </tr>
                                                </thead>
                                                <tbody class="checkout__totals-products">
                                                    <template v-for="item in $store.state.cart.items">
                                                        <tr v-if="item.merchant.id === mrch.id" :key="item.id">
                                                            <td>{{ item.label }} × {{ item.quantity }}</td>
                                                            <td>{{ $price(item.total) }}</td>
                                                        </tr>
                                                    </template>
                                                </tbody>
                                            </table>
                                        </div>
                                        <table class="checkout__totals">
                                            <tbody v-if="$store.state.cart.totals.length > 0" class="checkout__totals-subtotals">
                                                <tr>
                                                    <th>Subtotal</th>
                                                    <td>{{ $price($store.state.cart.subtotal) }}</td>
                                                </tr>
                                                <tr v-for="(total, index) in $store.state.cart.totals" :key="index">
                                                    <th>{{ total.title }}</th>
                                                    <td>{{ $price(total.price) }}</td>
                                                </tr>
                                            </tbody>
                                            <tfoot class="checkout__totals-footer">
                                                <tr>
                                                    <th style="vertical-align: top;">Total</th>
                                                    <td>
                                                        <template v-if="$store.state.cart.token === 'WSOL'">◎{{ $store.state.cart.tokenQuote }}<br/><p class="text-secondary" style="font-size: 12px;">{{ $price($store.state.cart.total) }}</p></template>
                                                        <template v-else>{{ $price($store.state.cart.total) }}</template>
                                                    </td>
                                                </tr>
                                            </tfoot>
                                        </table>
                                    </template>
                                    <template v-else>
                                        <div class="text-center" style="font-size: 1.25em;"><template v-if="$store.state.cart.merchants.length > 0">{{ $store.state.cart.merchants[0].label }}</template></div>
                                        <table class="checkout__totals">
                                            <thead class="checkout__totals-header">
                                                <tr>
                                                    <th>Product</th>
                                                    <th>Total</th>
                                                </tr>
                                            </thead>
                                            <tbody class="checkout__totals-products">
                                                <tr v-for="item in $store.state.cart.items" :key="item.id">
                                                    <td>{{ item.label }} × {{ item.quantity }}</td>
                                                    <td>{{ $price(item.total) }}</td>
                                                </tr>
                                            </tbody>
                                            <tbody v-if="$store.state.cart.totals.length > 0" class="checkout__totals-subtotals">
                                                <tr>
                                                    <th>Subtotal</th>
                                                    <td>{{ $price($store.state.cart.subtotal) }}</td>
                                                </tr>
                                                <tr v-for="(total, index) in $store.state.cart.totals" :key="index">
                                                    <th>{{ total.title }}</th>
                                                    <td>{{ $price(total.price) }}</td>
                                                </tr>
                                            </tbody>
                                            <tfoot class="checkout__totals-footer">
                                                <tr>
                                                    <th style="vertical-align: top;">Total</th>
                                                    <td>
                                                        <template v-if="$store.state.cart.token === 'WSOL'">◎{{ $store.state.cart.tokenQuote }}<br/><p class="text-secondary" style="font-size: 12px;">{{ $price($store.state.cart.total) }}</p></template>
                                                        <template v-else>{{ $price($store.state.cart.total) }}</template>
                                                    </td>
                                                </tr>
                                            </tfoot>
                                        </table>
                                    </template>
                                    <div class="payment-methods">
                                        <ul class="payment-methods__list">
                                            <Collapse
                                                v-for="(payment, index) in payments"
                                                :key="index"
                                                v-slot="{ itemClasses, contentClasses }"
                                                :is-open="currentPayment === payment.key"
                                                item-open-class="payment-methods__item--active"
                                            >
                                                <li :class="['payment-methods__item', itemClasses]">
                                                    <label class="payment-methods__item-header">
                                                        <span class="payment-methods__item-radio input-radio">
                                                            <span class="input-radio__body">
                                                                <input
                                                                    type="radio"
                                                                    class="input-radio__input"
                                                                    name="checkout_payment_method"
                                                                    :value="payment.key"
                                                                    :checked="currentPayment === payment.key"
                                                                    @change="handlePaymentChange"
                                                                    @click="handlePaymentClick"
                                                                >
                                                                <span class="input-radio__circle" />
                                                            </span>
                                                        </span>
                                                        <span class="payment-methods__item-title">
                                                            {{ payment.title }}
                                                        </span>
                                                    </label>
                                                    <div :class="['payment-methods__item-container', contentClasses]">
                                                        <div class="payment-methods__item-description text-muted">
                                                            {{ payment.description }}
                                                        </div>
                                                        <template v-if="payment.key === 'AtellixPay'">
                                                            <atellix-pay></atellix-pay>
                                                        </template>
                                                        <template v-else-if="payment.key === 'AuthorizeNet'">
                                                            <authorize-net :cardData="cardData"></authorize-net>
                                                        </template>
                                                    </div>
                                                </li>
                                            </Collapse>
                                        </ul>
                                    </div>
                                    <div>
                                        <p>
                                            The Atellix Network's
                                            <AppLink :to="$url.terms()">
                                                terms and conditions
                                            </AppLink>
                                            apply to this purchase.
                                        </p>
                                    </div>
                                    <button @click="handlePlaceOrder" :class="[
                                        'btn btn-primary btn-xl btn-block',
                                        {'btn-loading': paymentProcessing}
                                    ]">
                                        Place Order
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </client-only>
    </div>
</template>

<script lang="ts">

import { Vue, Component } from 'vue-property-decorator'
import { State } from 'vuex-class'
import { IPayment, IPaymentCard } from '~/interfaces/payment'
import { RootState } from '~/store'
import { Cart } from '~/interfaces/cart'
import { IAddress } from '~/interfaces/address'
import { create, optional, test, enforce } from 'vest'
import PageHeader from '~/components/shared/page-header.vue'
import AppLink from '~/components/shared/app-link.vue'
import Collapse from '~/components/shared/collapse.vue'
import AtellixPay from '~/components/payment/atellix_pay.vue'
import AuthorizeNet from '~/components/payment/authorize_net.vue'
import Check9x7Svg from '~/svg/check-9x7.svg'
import dataShopPayments from '~/data/shopPayments'
import parsePhoneNumber from 'libphonenumber-js'
import MaskedInput from 'vue-maskedinput'
import $solana from '@/api/solana-client'
import $geodata from '@/api/geodata'
import validator from 'validator'
import theme from '~/data/theme'

function defaultAddress(): IAddress {
    return {
        firstName: '',
        lastName: '',
        company: '',
        email: '',
        phone: '',
        city: '',
        region: '',
        postcode: '',
        address: '',
        address2: '',
        country: 'us',
    }
}

@Component({
    components: { PageHeader, AppLink, Check9x7Svg, Collapse, MaskedInput, AuthorizeNet, AtellixPay },
    head () {
        return {
            title: 'Checkout'
        }
    },
    async asyncData ({ store }): Promise<void> {
        store.dispatch('shop/setMerchant', { merchant: theme.merchant })
    }
})

export default class Page extends Vue {
    @State((store: RootState) => store.cart) cart!: Cart
    currentPayment: string = dataShopPayments[0].key
    payments: IPayment[] = dataShopPayments
    paymentProcessing: boolean = false
    clickTimer: any = null
    shippingAddress: IAddress = defaultAddress()
    billingAddress: IAddress = defaultAddress()
    billingAddressError: any = {}
    sameAddress: boolean = true
    usStatesList: any[] = $geodata.us_states_list()
    cardData: IPaymentCard = {
        cardNumber: '',
        cardExpires: '',
        cardSecurityCode: '',
    }

    // noinspection JSUnusedGlobalSymbols
    beforeMount () {
        if (this.cart.quantity < 1) {
            this.$router.push(this.$url.cart())
        }
    }

    mounted () {
        this.paymentProcessing = true
        var thiz = this
        this.$store.dispatch('cart/setShipping', {}).then(() => {
            console.log('Set Shipping')
            thiz.paymentProcessing = false
        })
    }

    handlePaymentChange (event: InputEvent) {
        if (event.target instanceof HTMLInputElement) {
            this.currentPayment = event.target.value
        }
    }

    // prevents unwanted scrolling
    handlePaymentClick (event: InputEvent) {
        const input = event.target
        clearTimeout(this.clickTimer)
        if (input instanceof HTMLInputElement) {
            input.blur()
            this.clickTimer = setTimeout(() => {
                input.focus()
            }, 500)
        }
    }

    validateCheckout(): boolean {
        console.log('Validate Checkout')
        const suite = create((data) => {
            optional(['company', 'phone', 'address2'])
            test('firstName', 'First name is required', () => { enforce(data.firstName).isNotBlank() })
            test('lastName', 'Last name is required', () => { enforce(data.lastName).isNotBlank() })
            test('email', 'Invalid email', () => { enforce(data.email).condition((value: string) => { return validator.isEmail(value) }) })
            if (data.phone) {
                test('phone', 'Invalid phone', () => { enforce(data.phone).condition((value: string) => {
                    const phoneNumber = parsePhoneNumber(value, 'US')
                    if (phoneNumber) {
                        return phoneNumber.isValid()
                    } else {
                        return false
                    }
                }) })
            }
            test('address', 'Address is required', () => { enforce(data.address).isNotBlank() })
            test('city', 'City is required', () => { enforce(data.city).isNotBlank() })
            test('region', 'Invalid state', () => { enforce(data.region).condition((value: string) => {
                if (!value) { return false }
                var states: any = {}
                $geodata.us_states_list().map(s => { states[s[0]] = s[1] })
                return value in states
            }) })
            test('postcode', 'Invalid zipcode', () => { enforce(data.postcode).matches(/^\d{5}$/) })
        })
        const results = suite(this.billingAddress)
        //console.log(results)
        this.billingAddressError = {}
        Object.keys(results.tests).map((prop) => {
            if (!results.tests[prop].valid) {
                this.billingAddressError[prop] = true
            }
        })
        return results.valid
    }

    async processPayments(store: any): Promise<any> {
        if (!this.validateCheckout()) {
            return
        }
        if (this.currentPayment === 'AtellixPay') {
            //console.log('AtellixPay Checkout: ' + store.state.wallet.publicKey)
            if (!store.state.wallet.connected) {
                console.log('AtellixPay Wallet Not Connected')
                return
            }
        }
        var shipping: IAddress
        if (this.sameAddress) {
            shipping = this.billingAddress
        } else {
            shipping = {
                ...this.shippingAddress,
                'firstName': this.billingAddress['firstName'],
                'lastName': this.billingAddress['lastName'],
                'company': this.billingAddress['company'],
                'phone': this.billingAddress['phone'],
                'email': this.billingAddress['email'],
            }
        }
        const billing = {
            ...this.billingAddress,
            'firstName': '',
            'lastName': '',
            'company': '',
            'phone': '',
            'email': '',
        }
        var paymentMethod: any = {}
        if (this.currentPayment === 'AtellixPay') {
            store.state.cart.merchants.map((r: any) => { paymentMethod[r.id] = 'atellixpay' })
        } else if (this.currentPayment === 'AuthorizeNet') {
            store.state.cart.merchants.map((r: any) => { paymentMethod[r.id] = 'authorizenet' })
        }
        await store.dispatch('cart/prepareCheckout', {
            'shippingAddress': shipping,
            'billingAddress': billing,
            'paymentMethod': paymentMethod,
        })
        if (this.currentPayment === 'AtellixPay') {
            const merchantToken = 'USDV'
            const orders: any[] = []
            const orderParams: any[] = []
            for (let i = 0; i < store.state.cart.payments.length; i++) {
                const orderUuid = store.state.cart.payments[i].data['uuid']
                const order = await $solana.client.getOrder(orderUuid)
                const dcm = order.tokens[merchantToken].decimals
                const tknTotal = $solana.math.evaluate('prc * 10^dcm', { prc: order.order_data.priceTotal, dcm: dcm })
                const params: any = {
                    'swap': false,
                    'wrapSOL': false,
                    'tokensTotal': tknTotal.toString(),
                }
                const paymentToken = store.state.cart.token
                if (paymentToken !== merchantToken) {
                    const swapKey = merchantToken + '-' + paymentToken
                    params['swap'] = true
                    params['swapKey'] = swapKey
                    if (paymentToken === 'WSOL') {
                        const wrapAmount = Number($solana.math.evaluate('amt * 1.025 * (10 ^ dcm)', {
                            amt: store.state.cart.tokenQuote,
                            dcm: order.tokens[paymentToken].decimals
                        }).toString())
                        params['wrapSOL'] = true
                        params['wrapAmount'] = wrapAmount.toFixed(0)
                    }
                }
                orders.push(order)
                orderParams.push(params)
            }
            console.log('AtellixPay Order Ready')
            var orderList: any[] = []
            orders.map((order) => {orderList.push(order.order_data)})
            $solana.client.updateNetData(orders[0].net_data)
            $solana.client.updateSwapData(orders[0].swap_data)
            $solana.client.updateOrderData(orderList)
            //console.log('Token: ' + token + ' Decimals: ' + dcm + ' Price Total: ' + order.order_data.priceTotal)
            //console.log(orderParams)
            const res = await $solana.client.merchantCheckout(orderParams)
            //await store.dispatch('cart/getCart', {})
            console.log('Solana Transaction Result')
            console.log(res)
            if (typeof res === 'object' && res.result === 'error') {
                Vue.notify({
                    type: 'warn',
                    text: res.error,
                })
                return
            }
        } else if (this.currentPayment === 'AuthorizeNet') {
            for (let i = 0; i < store.state.cart.payments.length; i++) {
                const paymentUuid = store.state.cart.payments[i].data['uuid']
                const spec = {
                    'payment_uuid': paymentUuid,
                    'card': this.cardData,
                    'shipping': shipping,
                    'billing': billing,
                }
                const res = await this.$shopApi.processAuthorizeNetPayment(spec)
                console.log('AuthorizeNet Payment Result')
                console.log(res)
                if (res.result !== 'ok') {
                    Vue.notify({
                        type: 'warn',
                        text: res.error,
                    })
                    return
                }
            }
        }
        const uuid: string = await store.dispatch('cart/checkoutComplete', {})
        this.$router.push(this.$url.thankyou(uuid))
    }

    handlePlaceOrder (event: InputEvent) {
        //console.log('Place Order...')
        //console.log(this.paymentProcessing)
        if (!this.paymentProcessing) {
            this.paymentProcessing = true
            var thiz = this
            this.processPayments(this.$store).then(() => {
                thiz.paymentProcessing = false
                console.log('Checkout Done')
            })
        }
    }
}

</script>
