import Vue from 'vue'
import { Plugin } from '@nuxt/types'
import VueNativeSock from 'vue-native-websocket'

interface SocketPlugin {
    install: any
}

const plugin: Plugin = (spec: any) => {
    Vue.use((VueNativeSock as unknown) as SocketPlugin, '', {
        connectManually: true,
        format: 'json',
        reconnection: true,
        reconnectionAttempts: 12,
        reconnectionDelay: 5000
    })
}

export default plugin

