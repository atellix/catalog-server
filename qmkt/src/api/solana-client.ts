import { PublicKey, Keypair, Connection, Transaction, SystemProgram, ComputeBudgetProgram } from '@solana/web3.js'
import { WalletAdapterNetwork, WalletNotConnectedError } from '@solana/wallet-adapter-base'
import { PhantomWalletAdapter } from '@solana/wallet-adapter-phantom'
import { SolflareWalletAdapter } from '@solana/wallet-adapter-solflare'
import { BackpackWalletAdapter } from '@solana/wallet-adapter-backpack'
import { GlowWalletAdapter } from '@solana/wallet-adapter-glow'
import { CoinbaseWalletAdapter } from '@solana/wallet-adapter-coinbase'
import { ExodusWalletAdapter } from '@solana/wallet-adapter-exodus'
import { SlopeWalletAdapter } from '@solana/wallet-adapter-slope'
import { TrustWalletAdapter } from '@solana/wallet-adapter-trust'
import { AnchorProvider, Program, BN, setProvider } from '@project-serum/anchor'
import {
    getAccount,
    TOKEN_PROGRAM_ID,
    ASSOCIATED_TOKEN_PROGRAM_ID,
    createAssociatedTokenAccountInstruction,
    createSyncNativeInstruction,
    createCloseAccountInstruction,
    TokenAccountNotFoundError
} from '@solana/spl-token'
import { v4 as uuidv4, parse as uuidParse } from 'uuid'
import { create, all } from 'mathjs'
import bigintConv from 'bigint-conversion'
import { DateTime } from 'luxon'
import { Buffer } from 'buffer'
import bs58 from 'bs58'
import { SOLANA_API_URL, ATELLIX_API_URL } from './constants'

const ANCHOR_IDL: { [key: string]: any } = {
    'atx-net-authority': require('@/api/idl/net_authority.json'),
    'atx-swap-contract': require('@/api/idl/swap_contract.json'),
    'token-agent': require('@/api/idl/token_agent.json'),
    'token-delegate': require('@/api/idl/token_delegate.json'),
}

async function postData(url: string = "", data: any = {}): Promise<any> {
    const response = await fetch(url, {
        method: "POST",
        //mode: "cors",
        cache: "no-cache",
        //credentials: "include",
        headers: { "Content-Type": "application/json" },
        redirect: "manual",
        referrerPolicy: "no-referrer",
        body: JSON.stringify(data),
    })
    return response.json()
}

function math() {
    return create(all, {
        number: 'BigNumber',
        precision: 64
    })
}

const solana_math = math()

export interface MerchantCheckoutParams {
    swap: boolean,
    swapKey?: string,
    wrapSOL: boolean,
    wrapAmount?: BN,
    tokensTotal: number,
}

class SolanaClient {
    provider?: AnchorProvider
    program: { [key: string]: any }
    oracleQuote: { [key: string]: string }
    registerFn: any
    netData: any
    orderData: any[]
    orderSeq?: number
    tokenData: any
    swapData: any

    constructor () {
        this.program = {}
        this.oracleQuote = {}
        this.orderData = []
    }

    updateNetData(data: any) {
        this.netData = data
    }

    updateOrderData(data: any[]) {
        this.orderData = data
    }

    updateTokenData(data: any) {
        this.tokenData = data
    }

    updateSwapData(data: any) {
        this.swapData = data
    }

    getWalletAdapters(network: WalletAdapterNetwork | undefined) {
        return [
            new PhantomWalletAdapter(),
            new SolflareWalletAdapter({ network }),
            new BackpackWalletAdapter(),
            new GlowWalletAdapter(),
            new CoinbaseWalletAdapter(),
            new ExodusWalletAdapter(),
            new SlopeWalletAdapter(),
            new TrustWalletAdapter(),
        ]
    }

    getWallets() {
        const network = WalletAdapterNetwork.Mainnet
        return this.getWalletAdapters(network)
    }

    getProvider(adapter: any) {
        const apiUrl = SOLANA_API_URL
        const wallet = {
            publicKey: adapter.publicKey,
            signTransaction: function (transaction: Transaction) { return adapter.signTransaction(transaction) },
            signAllTransactions: function (transactions: Transaction[]) {
                if (!adapter.connected) { throw new WalletNotConnectedError() }
                return adapter.wallet.signAllTransactions(transactions)
            }
        }
        const connection = new Connection(apiUrl, {
            commitment: 'confirmed',
            confirmTransactionInitialTimeout: 180000,
        })
        const provider = new AnchorProvider(connection, wallet, { commitment: 'confirmed' })
        this.provider = provider
        return provider
    }

    async associatedTokenAddress(walletAddress: PublicKey, tokenMintAddress: PublicKey) {
        const addr = await PublicKey.findProgramAddress(
            [walletAddress.toBuffer(), TOKEN_PROGRAM_ID.toBuffer(), tokenMintAddress.toBuffer()],
            ASSOCIATED_TOKEN_PROGRAM_ID
        )
        const res = { 'pubkey': await addr[0].toString(), 'nonce': addr[1] }
        return res
    }

    async programAddress(inputs: any[], program: PublicKey) {
        const addr = await PublicKey.findProgramAddress(inputs, program)
        const res = { 'pubkey': await addr[0].toString(), 'nonce': addr[1] }
        return res
    }

    loadProgram(programKey: string) {
        const provider = this.provider as AnchorProvider
        setProvider(provider)
        if (typeof this.program[programKey] === 'undefined') {
            let programPK = new PublicKey(ANCHOR_IDL[programKey]['metadata']['address'])
            this.program[programKey] = new Program(ANCHOR_IDL[programKey], programPK)
        }
        return this.program[programKey]
    }

    async getAccountData(programKey: string, accountType: string, accountPK: PublicKey) {
        const provider = this.provider as AnchorProvider
        setProvider(provider)
        let program
        if (typeof this.program[programKey] === 'undefined') {
            program = this.program[programKey]
        } else {
            let programPK = new PublicKey(ANCHOR_IDL[programKey]['metadata']['address'])
            program = new Program(ANCHOR_IDL[programKey], programPK)
            this.program[programKey] = program
        }
        const data = await program.account[accountType].fetch(accountPK)
        return data
    }

    async getAccountInfo(accountPK: PublicKey) {
        const provider = this.provider as AnchorProvider
        setProvider(provider)
        return await provider.connection.getAccountInfo(accountPK)
    }

    async getLamports(walletPK: PublicKey): Promise<number> {
        const provider = this.provider as AnchorProvider
        setProvider(provider)
        const walletInfo = await provider.connection.getAccountInfo(walletPK, 'confirmed')
        if (walletInfo && typeof walletInfo['lamports'] !== 'undefined') {
            return walletInfo.lamports
        }
        return Number(0)
    }

    async getTokenBalance(mintPK: PublicKey, walletPK: PublicKey): Promise<string> {
        const provider = this.provider as AnchorProvider
        setProvider(provider)
        const tokenInfo = await this.associatedTokenAddress(walletPK, mintPK)
        const tokenPK = new PublicKey(tokenInfo.pubkey)
        var amount = '0'
        try {
            const tokenAccount = await getAccount(provider.connection, tokenPK)
            //console.log('Token Account - Wallet: ' + wallet + ' Mint: ' + mint)
            //console.log(tokenAccount)
            amount = tokenAccount.amount.toString()
        } catch (error) {
            if (error instanceof TokenAccountNotFoundError) {
                // Do nothing
            } else {
                console.error(error)
            }
        }
        return amount
    }

    async getTokenBalances(tokens: string[], wallet: string): Promise<{ [key: string]: string }> {
        var balances: { [key: string]: string } = {}
        const walletKey = new PublicKey(wallet)
        for (var t = 0; t < tokens.length; t++) {
            const tk = tokens[t]
            if (this.tokenData[tk]) {
                try {
                    balances[tk] = await this.getTokenBalance(new PublicKey(this.tokenData[tk].mint), walletKey)
                } catch (error) {
                    break
                }
            }
        }
        // Get SOL balance and combine with Wrapped SOL balance
        var solBalance: number = await this.getLamports(walletKey)
        balances['SOL'] = solBalance.toString()
        if (typeof balances['WSOL'] !== 'undefined') {
            solBalance = solBalance + Number(balances['WSOL'])
            balances['WSOL'] = solBalance.toString()
        }
        return balances
    }

    async hasTokenAccount(ataPK: PublicKey) {
        const provider = this.provider as AnchorProvider
        setProvider(provider)
        try {
            await getAccount(provider.connection, ataPK)
        } catch (error) {
            return false
        }
        return true
    }

    async createTokenAccount(mint: PublicKey, wallet: PublicKey) {
        const provider = this.provider as AnchorProvider
        setProvider(provider)
        const tokenInfo = await this.associatedTokenAddress(wallet, mint)
        const tokenPK = new PublicKey(tokenInfo.pubkey)
        const tx = new Transaction()
        tx.add(createAssociatedTokenAccountInstruction(wallet, tokenPK, wallet, mint))
        provider.opts['skipPreflight'] = true
        return await provider.registerAndSend(tx, async (sig): Promise<boolean> => {
            return true
        })
    }

    async getPaymentTokens(): Promise<void> {
        const url = ATELLIX_API_URL
        const tokens = await postData(url, {
            'command': 'get_tokens',
        })
        this.updateNetData(tokens.net_data)
        this.updateSwapData(tokens.swap_data)
        return tokens
    }

    async getOrder(orderUuid: string): Promise<any> {
        const url = ATELLIX_API_URL
        const orderSpec = await postData(url, {
            'command': 'load',
            'mode': 'order',
            'uuid': orderUuid,
        })
        return orderSpec
    }

    async registerSignature(sig: string, orderUuid: string, pubkey: string): Promise<boolean> {
        const url = ATELLIX_API_URL
        const register = await postData(url, {
            'command': 'register_signature',
            'op': 'checkout',
            'sig': sig,
            'uuid': orderUuid,
            'timezone': Intl.DateTimeFormat().resolvedOptions().timeZone,
            'user_key': pubkey,
        })
        //console.log('Register Result')
        //console.log(register)
        return (register['result'] === 'ok') ? true : false
    }

    async merchantCheckout(params: MerchantCheckoutParams[]) {
        //console.log('Checkout')
        //console.log(params)
        const provider = this.provider as AnchorProvider
        setProvider(provider)
        let tokenAgentPK = new PublicKey(this.netData.program['token-agent'])
        let tokenAgent = new Program(ANCHOR_IDL['token-agent'], tokenAgentPK)
        let netAuth = new PublicKey(this.netData.program['atx-net-authority'])
        let orders: Transaction[] = []
        for (let i = 0; i < this.orderData.length; i++) {
            let tokenMint = new PublicKey(this.orderData[i].tokenMint)
            let destPK = new PublicKey(this.orderData[i].merchantWallet)
            let merchantAP = new PublicKey(this.orderData[i].merchantApproval)
            let merchantTK = await this.associatedTokenAddress(destPK, tokenMint)
            let feesPK = new PublicKey(this.orderData[i].feesAccount)
            let feesTK = await this.associatedTokenAddress(feesPK, tokenMint)

            let rootKey = await this.programAddress([tokenAgentPK.toBuffer()], tokenAgentPK)
            let walletToken = await this.associatedTokenAddress(provider.wallet.publicKey, tokenMint)
            let tokenAccount = new PublicKey(walletToken.pubkey)

            let operationSpec: any = {
                accounts: {
                    netAuth: netAuth,
                    rootKey: new PublicKey(rootKey.pubkey),
                    merchantApproval: merchantAP,
                    merchantToken: new PublicKey(merchantTK.pubkey),
                    userKey: provider.wallet.publicKey,
                    tokenProgram: TOKEN_PROGRAM_ID,
                    tokenAccount: tokenAccount,
                    feesAccount: new PublicKey(feesTK.pubkey),
                }
            }
        
            let bump_root = 0
            let bump_inb = 0
            let bump_out = 0
            let bump_dst = 0
            let swapDirection = false
            let tx = new Transaction()
            let unwrapSOL = false
            let walletTokenPK
            if (params[i].swap) {
                let swapSpec = this.swapData[params[i].swapKey as string]
                swapDirection = swapSpec.swapDirection
                let swapContractPK = new PublicKey(this.netData.program['atx-swap-contract'])
                let tokenMint1 = new PublicKey(swapSpec.tokenMint1)
                let tokenMint2 = new PublicKey(swapSpec.tokenMint2)
                let swapDataPK = new PublicKey(swapSpec.swapData)
                let swapFeesTK = new PublicKey(swapSpec.feesToken)
                let swapId = 0 // TODO: Make this dynamic
                let buf = Buffer.alloc(2)
                buf.writeInt16LE(swapId)
                let swapData
                if (swapDirection) {
                    swapData = await this.programAddress([tokenMint1.toBuffer(), tokenMint2.toBuffer(), buf], swapContractPK)
                } else {
                    swapData = await this.programAddress([tokenMint2.toBuffer(), tokenMint1.toBuffer(), buf], swapContractPK)
                }
                let tokData1 = await this.associatedTokenAddress(swapDataPK, tokenMint1)
                let tokData2 = await this.associatedTokenAddress(swapDataPK, tokenMint2)
                let agentToken = await this.associatedTokenAddress(new PublicKey(rootKey.pubkey), tokenMint)
                //console.log('Root Key: ' + rootKey.pubkey)
                tokenAccount = new PublicKey(agentToken.pubkey)
                //console.log('Token Account: ' + agentToken.pubkey)
                walletToken = await this.associatedTokenAddress(provider.wallet.publicKey, tokenMint1)
                walletTokenPK = new PublicKey(walletToken.pubkey)
                bump_root = swapData.nonce
                bump_inb = tokData1.nonce
                bump_out = tokData2.nonce
                bump_dst = agentToken.nonce
                let remainAccts = [
                    { pubkey: walletTokenPK, isWritable: true, isSigner: false },
                    { pubkey: swapContractPK, isWritable: false, isSigner: false },
                    { pubkey: swapDataPK, isWritable: true, isSigner: false },
                    { pubkey: new PublicKey(tokData1.pubkey), isWritable: true, isSigner: false },
                    { pubkey: new PublicKey(tokData2.pubkey), isWritable: true, isSigner: false },
                    { pubkey: swapFeesTK, isWritable: true, isSigner: false },
                ]
                if (typeof swapSpec['oracleChain'] !== 'undefined') {
                    remainAccts.push({ pubkey: new PublicKey(swapSpec.oracleChain), isWritable: false, isSigner: false })
                }
                operationSpec['accounts']['tokenAccount'] = tokenAccount
                operationSpec['remainingAccounts'] = remainAccts
                if (params[i].wrapSOL) {
                    //console.log('Wrap Estimate: ' + params.wrapAmount)
                    let wrapAmount = new BN(params[i].wrapAmount)
                    let walletSOL = await this.getLamports(provider.wallet.publicKey)
                    if (Number(params[i].wrapAmount) > walletSOL) {
                        let minimumSOL = Number(0.01 * (10 ** 9))
                        wrapAmount = walletSOL - minimumSOL
                    }
                    let hasWSOL = await this.hasTokenAccount(walletTokenPK)
                    if (!hasWSOL) {
                        unwrapSOL = true // Unwrap the remaining SOL after the payment
                        //let size = AccountLayout.span
                        //let rent = await provider.connection.getMinimumBalanceForRentExemption(size)
                        //wrapAmount = wrapAmount - rent
                        tx.add(createAssociatedTokenAccountInstruction(
                            provider.wallet.publicKey,
                            walletTokenPK,
                            provider.wallet.publicKey,
                            tokenMint1,
                        ))
                    }
                    //console.log('Wrap Amount: ' + wrapAmount.toString())
                    tx.add(SystemProgram.transfer({
                        fromPubkey: provider.wallet.publicKey,
                        lamports: wrapAmount.toString(),
                        toPubkey: walletTokenPK,
                    }))
                    tx.add(createSyncNativeInstruction(walletTokenPK))
                }
            }
            let paymentUuid = uuidParse(this.orderData[i].orderId)
            let amount = new BN(params[i].tokensTotal)
            //console.log('Amount: ' + amount.toString())
            tx.add(tokenAgent.instruction.merchantPayment(
                merchantTK.nonce,                        // inp_merchant_nonce (merchant associated token account nonce)
                rootKey.nonce,                           // inp_root_nonce
                new BN(paymentUuid),                     // inp_payment_id
                amount,                                  // inp_amount
                params[i].swap,                             // inp_swap
                swapDirection,                           // inp_swap_direction
                0,                                       // inp_swap_mode
                bump_root,                               // inp_swap_data_nonce
                bump_inb,                                // inp_swap_inb_nonce
                bump_out,                                // inp_swap_out_nonce
                bump_dst,                                // inp_swap_dst_nonce
                operationSpec,
            ))
            if (unwrapSOL) {
                tx.add(createCloseAccountInstruction(
                    walletTokenPK as PublicKey,
                    provider.wallet.publicKey,
                    provider.wallet.publicKey,
                ))
            }
            orders.push(tx)
        }
        let txid: string[] = ['']
        try {
            provider.opts['skipPreflight'] = true
            if (orders.length > 1) {
                var orderList: {tx: Transaction}[] = []
                orders.map((order) => {
                    orderList.push({tx: order})
                })
                this.orderSeq = 0
                console.log(orderList)
                txid = await provider.registerAndSendAll(orderList, async (sig: any) => {
                    console.log(sig)
                    const sigtxt = bs58.encode(new Uint8Array(sig as Buffer))
                    const seq = this.orderSeq as number
                    const success: boolean = await this.registerSignature(sigtxt, this.orderData[seq].orderId, provider.wallet.publicKey.toString())
                    this.orderSeq = (this.orderSeq as number) + 1
                    return success
                })
            } else if (orders.length === 1) {
                txid[0] = await provider.registerSendAndConfirm(orders[0], async (sig) => {
                    const sigtxt = bs58.encode(new Uint8Array(sig as Buffer))
                    const success: boolean = await this.registerSignature(sigtxt, this.orderData[0].orderId, provider.wallet.publicKey.toString())
                    return success
                })
            }
        } catch (error) {
            return {
                'result': 'error',
                'error': error
            }
        }
        //console.log('Subscribed: ' + subscrDataPK.toString())
        return {
            'result': 'ok',
            'uuid': this.orderData[0].orderId,
            'transaction_sig': txid[0],
        }
    }

    async quoteAmount(toToken: any, fromToken: any, swapInfo: any, fromAmount: string, swapKey: string, orderType: string = 'sell') {
        //console.log(fromToken)
        //console.log('quoteAmount: ' + swapKey)
        //console.log(toToken, fromToken, fromAmount)
        //console.log('Swap Data: ' + swapInfo.swapData)
        let swapData = await this.getAccountData('atx-swap-contract', 'swapData', new PublicKey(swapInfo.swapData))
        //console.log(swapData)
        let swapToken
        if (swapInfo.swapDirection) {
            swapToken = swapData.inbTokenData
        } else {
            swapToken = swapData.outTokenData
        }
        let useOracle = swapToken.oracleRates
        let oracleInverse = swapToken.oracleInverse
        let oracleMax = swapToken.oracleMax
        let swapRate
        let baseRate
        if (!fromAmount.length) {
            fromAmount = '0'
        }
        fromAmount = fromAmount.replace(/,/g, '')
        if (useOracle) {
            //console.log('Use Oracle')
            let decimalDiff = solana_math.evaluate('idc - odc', {
                idc: fromToken.decimals,
                odc: toToken.decimals,
            })
            decimalDiff = solana_math.abs(decimalDiff)
            //console.log('Current Oracle Quote: ' + this.oracleQuote[swapInfo['oracleTrack']])
            var oracleVal = Number.parseFloat(this.oracleQuote[swapInfo['oracleTrack']]).toFixed(6)
            //console.log('Oracle Value: ' + oracleVal)
            if (oracleMax) {
                oracleVal = solana_math.max(
                    solana_math.evaluate('val', { val: oracleVal }),
                    solana_math.evaluate('val / (10 ^ 8)', { val: swapToken.rateSwap.toString() })
                )
            }
            if (oracleInverse) {
                baseRate = solana_math.evaluate('10 ^ ddf', { ddf: decimalDiff })
                swapRate = oracleVal
            } else {
                swapRate = solana_math.evaluate('10 ^ ddf', { ddf: decimalDiff })
                baseRate = oracleVal
            }
        } else {
            swapRate = swapToken.rateSwap.toString()
            baseRate = swapToken.rateBase.toString()
        }
        let feeRate = swapToken.feesBps.toString()
        let fnOutput
        //console.log('Input: ' + fromAmount)
        //console.log('Use Oracle: ' + useOracle + ' Inverse: ' + oracleInverse)
        //console.log('Swap Rate: ' + swapRate + ' Base Rate: ' + baseRate + ' Fees BPS: ' + feeRate)
        //console.log('Inb Decimals: ' + fromToken.decimals + ' Out Decimals: ' + toToken.decimals)
        let fromTokens
        let viewStr
        if (orderType === 'sell') {
            let inAmount = solana_math.evaluate('inp * (10 ^ dcm)', {
                inp: fromAmount,
                dcm: fromToken.decimals
            })
            let inTokens = solana_math.floor(inAmount)
            fromTokens = inTokens
            //console.log('Sell Tokens: ' + inTokens)
            fnOutput = solana_math.evaluate('((inp - (inp * (fee / 10000))) * brt) / srt', {
                inp: inTokens,
                fee: feeRate,
                brt: baseRate,
                srt: swapRate
            })
            fnOutput = solana_math.floor(fnOutput)
            let viewOutput = solana_math.evaluate('out / (10 ^ dcm)', {
                out: fnOutput,
                dcm: toToken.decimals
            })
            viewStr = Number.parseFloat(viewOutput.toString()).toFixed(toToken.viewDecimals)
        } else if (orderType === 'buy') {
            let outAmount = solana_math.evaluate('inp * (10 ^ dcm)', {
                inp: fromAmount,
                dcm: toToken.decimals
            })
            let outTokens = solana_math.floor(outAmount)
            fromTokens = outTokens
            //console.log('Buy Tokens: ' + outTokens)
            fnOutput = solana_math.evaluate('((out + (out * (fee / 10000))) * srt) / brt', {
                out: outTokens,
                fee: feeRate,
                brt: baseRate,
                srt: swapRate
            })
            fnOutput = solana_math.floor(fnOutput)
            let viewOutput = solana_math.evaluate('out / (10 ^ dcm)', {
                out: fnOutput,
                dcm: fromToken.decimals
            })
            viewStr = Number.parseFloat(viewOutput.toString()).toFixed(fromToken.viewDecimals)
        }
        //console.log('Output: ' + fnOutput.toString() + ' View: ' + viewStr)
        //console.log('-')
        return {'amount': fnOutput.toString(), 'viewAmount': viewStr, 'fromAmountTokens': fromTokens.toString()}
    }
}

const solana = new SolanaClient()

export default {
    'client': solana,
    'math': solana_math,
}
    
