import { IOrder } from '~/interfaces/order'

const dataAccountOrderLoading: IOrder = {
    id: '',
    date: '',
    status: '',
    items: [],
    additionalLines: [],
    quantity: 0,
    subtotal: 0,
    total: 0,
    paymentMethod: '',
    shippingAddress: {
        firstName: '',
        lastName: '',
        email: '',
        phone: '',
        country: '',
        city: '',
        region: '',
        postcode: '',
        address: ''
    },
    billingAddress: {
        firstName: '',
        lastName: '',
        email: '',
        phone: '',
        country: '',
        city: '',
        region: '',
        postcode: '',
        address: ''
    }
}

export default dataAccountOrderLoading
