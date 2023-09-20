export interface IPayment {
    key: string;
    title: string;
    description: string;
}

export interface IPaymentCard {
    cardNumber: string;
    cardExpires: string;
    cardSecurityCode: string;
}
