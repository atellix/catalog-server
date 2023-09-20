<template>
    <div class="payment-wrapper">
        <div class="card" style="border: 0;">
            <div class="card-body" style="padding: 1em; padding-left: 1em;">
                <form>
                    <table style="width: 100%; margin-right: 10px;">
                        <tr>
                            <td colspan="2">
                                <p class="mb-0 pb-0">Card Number:</p>
                                <input v-model="cardData.cardNumber" name="cardNumber" autocomplete="cc-number" id="cc-number" type="text" class="form-control" style="width: 100%;" placeholder="Card number"/>
                            </td>
                        </tr>
                        <tr>
                            <td style="width: 50%;" class="pt-2 pr-2">
                                <p class="mb-0 pb-0">Expires:</p>
                                <masked-input v-model="cardData.cardExpires" placeholder="MM/YY" style="width: 100%;" pattern="11/11" name="cardExpiry" autocomplete="cc-exp" id="cc-exp" class="form-control" type="text"></masked-input>
                            </td>
                            <td style="width: 50%;" class="pt-2">
                                <p class="mb-0 pb-0">Security Code:</p>
                                <input v-model="cardData.cardSecurityCode" name="securityCode" id="cc-csc" type="text" class="form-control" style="width: 100%;" placeholder="Code"/>
                            </td>
                        </tr>
                    </table>
                </form>
            </div>
        </div>
    </div>
</template>

<script lang="ts">
import { Vue, Prop, Component } from 'vue-property-decorator'
import { IPaymentCard } from '~/interfaces/payment'
import MaskedInput from 'vue-maskedinput'

@Component({
    components: { MaskedInput }
})
export default class AuthorizeNet extends Vue {
    @Prop() cardData!: IPaymentCard
}

</script>
