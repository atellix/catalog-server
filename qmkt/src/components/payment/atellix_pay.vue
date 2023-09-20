<template>
    <div class="payment-wrapper">
        <div class="card" style="border: 0;">
            <div class="card-body" style="padding: 1em; height: 230px;">
                <wallet-multi-button :wallets="wallets" :autoConnect="true" ref="mainWallet"/>
                <div v-if="walletData.connected">
                    <div class="mt-3">
                        <h6>Token Account:</h6>
                        <table>
                            <tr>
                                <td>
                                    <template v-if="paymentToken === 'WSOL'"><img src="https://s2.coinmarketcap.com/static/img/coins/128x128/5426.png" height="40" width="40" style="border-radius: 50%; overflow: hidden;"/></template>
                                    <template v-else-if="paymentToken === 'USDV'"><img src="https://media.atellix.net/token/usdv.png" height="40" width="40"/></template>
                                    <template v-else-if="paymentToken === 'USDC'"><img src="https://s2.coinmarketcap.com/static/img/coins/128x128/3408.png" height="40" width="40"/></template>
                                    <template v-else-if="paymentToken === 'UXD'"><img src="https://media.atellix.net/token/uxd.png" height="40" width="40"/></template>
                                </td>
                                <td>
                                    <select v-model="paymentToken" style="height: 40px;">
                                        <option v-for="tkn in tokenList" :key="tkn.id" :value="tkn.id">{{ tkn.name }}</option>
                                    </select>
                                </td>
                            </tr>
                        </table>
                    </div>
                    <div class="mt-3">
                        <h6>Balance:</h6>
                        <template v-if="tokenData[paymentToken].stablecoin">$</template><template v-else-if="paymentToken === 'WSOL'">◎</template>{{ formatBalance(paymentToken, balance[paymentToken]) }}
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script lang="ts">
import { Vue, Component, Ref } from 'vue-property-decorator'
import { initWallet, WalletMultiButton } from 'solana-wallets-vue-2'
import 'solana-wallets-vue-2/styles.css'
import $solana from '@/api/solana-client'

@Component({
    components: { WalletMultiButton }
})

export default class AtellixPay extends Vue {
    wallets: any[] = $solana.client.getWallets()
    walletData: any = { connected: false }
    solanaReady: boolean = false
    socketConnected: boolean = false
    paymentToken: string = 'USDC'
    tokenList: any[] = []
    tokenData: any = {}
    swapData: any = {}
    balance: any = {}
    $socket: any

    formatBalance (token: string, balance: string | undefined) {
        if (typeof balance !== 'undefined') {
            const dcm = this.tokenData[token].decimals
            const vdc = this.tokenData[token].viewDecimals
            const res = $solana.math.evaluate('bal / 10^dcm', { bal: balance.toString(), dcm: dcm.toString() })
            return new Number(res).toLocaleString('en-US', { minimumFractionDigits: vdc, maximumFractionDigits: vdc })
        } else {
            return ''
        }
    }

    mounted () {
        $solana.client.loadProgram('atx-swap-contract')
        const total = Number(this.$store.state.cart.total).toFixed(2)
        const tokenOrder: string[] = ['USDC', 'USDV', 'WSOL']
        this.paymentToken = 'USDC'
        this.$store.commit('cart/updateTokenInfo', {
            token: this.paymentToken,
            tokenQuote: this.$store.state.cart.total,
        })
        this.walletData = (this.$refs.mainWallet as any).walletStore
        this.$watch(() => { return this.walletData.connected }, (val) => {
            console.log('Connected: ' + val)
            this.$store.commit('wallet/setWalletState', {
                connected: this.walletData.connected,
                publicKey: this.walletData.publicKey,
            })
            if (val && !this.solanaReady) {
                this.solanaReady = true
                $solana.client.getProvider(this.walletData)
                $solana.client.getTokenBalances(tokenOrder, this.walletData.publicKey).then((bals) => {
                    this.balance = bals
                })
            }
        })
        this.$watch(() => { return this.paymentToken }, (val) => {
            //console.log('New Payment Token: ' + val)
            if (this.tokenData[val].stablecoin) {
                this.$store.commit('cart/updateTokenInfo', {
                    token: val,
                    tokenQuote: this.$store.state.cart.total,
                })
            } else {
                const swapKey = 'USDV-' + val
                if (swapKey in this.swapData) {
                    const swdata = this.swapData[swapKey]
                    if (swdata.oracleTrack) {
                        $solana.client.quoteAmount(this.tokenData['USDV'], this.tokenData[val], swdata, total, swapKey, 'buy').then((quoteData) => {
                            const quote = Number(quoteData.viewAmount)
                            this.$store.commit('cart/updateTokenInfo', {
                                token: val,
                                tokenQuote: quote,
                            })
                        })
                    }
                }
            }
        })
        $solana.client.getPaymentTokens().then((tokenResult) => {
            for (var i = 0; i < tokenOrder.length; i++) {
                const tk: string = tokenOrder[i]
                this.tokenData[tk] = (tokenResult as any).tokens[tk]
                this.tokenList.push({
                    'id': tk,
                    'name': (tokenResult as any).tokens[tk].label,
                })
            }
            this.swapData = (tokenResult as any).swap_data
            $solana.client.updateTokenData(this.tokenData)
            $solana.client.updateSwapData(this.swapData)
            this.$store.subscribe((mutation, state) => {
                //console.log('Socket Event: ' + mutation.type)
                //console.log(mutation.payload)
                if (mutation.type === 'SOCKET_ONOPEN') {
                    console.log('Atellix websocket ready')
                    const swapKeys = Object.keys((tokenResult as any).swap_data)
                    for (var j = 0; j < swapKeys.length; j++) {
                        const sk = swapKeys[j]
                        const swp = this.swapData[sk]
                        if (swp.oracleTrack && !(swp.oracleTrack in state.oracleSubscr)) {
                            state.oracleSubscr[swp.oracleTrack] = true
                            this.$socket.sendObj({ 'command': 'subscribe', 'data': { 'channel': 'event/oracle/' + swp.oracleTrack }})
                        }
                    }
                } else if (mutation.type === 'SOCKET_ONCLOSE') {
                    console.log('Atellix websocket closed')
                } else if (mutation.type === 'SOCKET_ONERROR') {
                    console.log('Atellix websocket error')
                    console.log(mutation.payload)
                } else if (mutation.type === 'SOCKET_ONMESSAGE') {
                    const msg = state.socket.message
                    if (msg['event'] === 'channel_msg') {
                        //console.log('Channel: ' + msg['channel'] + ' - ' + JSON.stringify(msg['data']))
                        if (msg['channel'].startsWith('event/oracle/')) {
                            const oracle = msg['channel'].split('/')[2]
                            console.log('Oracle quote: ' + oracle + ': ' + msg['data']['quote'])
                            $solana.client.oracleQuote[oracle] = msg['data']['quote']
                            if (this.paymentToken !== 'USDV') {
                                const swapKey = 'USDV-' + this.paymentToken
                                if (swapKey in this.swapData) {
                                    const swdata = this.swapData[swapKey]
                                    if (swdata.oracleTrack) {
                                        $solana.client.quoteAmount(this.tokenData['USDV'], this.tokenData[this.paymentToken], swdata, total, swapKey, 'buy').then((quoteData) => {
                                            const quote = Number(quoteData.viewAmount)
                                            this.$store.commit('cart/updateTokenInfo', {
                                                token: this.paymentToken,
                                                tokenQuote: quote,
                                            })
                                        })
                                    }
                                }
                            }
                        }
                    }
                }
            })
            if (!this.socketConnected) {
                this.socketConnected = true
                Vue.prototype.$connect('wss://atx2.atellix.net/ws', { store: this.$store, format: 'json' })
            }
        })
    }
}

</script>
<style type="text/css">
.swv-button p {
    margin-top: 1rem;
}
</style>
