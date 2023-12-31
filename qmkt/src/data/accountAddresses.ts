import { IUserAddress } from '~/interfaces/address'

const dataAccountAddresses: IUserAddress[] = [
    {
        id: 1,
        default: true,
        firstName: 'Helena',
        lastName: 'Garcia',
        email: 'stroyka@example.com',
        phone: '38 972 588-42-36',
        country: 'Random Federation',
        city: 'Moscow',
        region: 'Region',
        postcode: '115302',
        address: 'ul. Varshavskaya, 15-2-178'
    },
    {
        id: 2,
        default: false,
        firstName: 'Jupiter',
        lastName: 'Saturnov',
        email: 'stroyka@example.com',
        phone: 'ZX 971 972-57-26',
        country: 'RandomLand',
        city: 'MarsGrad',
        region: 'Region',
        postcode: '4b4f53',
        address: 'Sun Orbit, 43.3241-85.239'
    }
]

export default dataAccountAddresses
