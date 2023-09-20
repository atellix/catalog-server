export interface IAddress {
    firstName: string;
    lastName: string;
    company?: string;
    email: string;
    phone: string;
    country: string;
    city: string;
    region: string;
    postcode: string;
    address: string;
    address2?: string;
}

export interface IUserAddress extends IAddress {
    id: number;
    default: boolean;
}
