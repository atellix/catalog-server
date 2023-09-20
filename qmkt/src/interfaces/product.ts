import { IBrand } from './brand'
import { IFilter } from './filter'
import { IFilterableList, IPaginatedList } from './list'
import { IShopCategory } from './category'
import { ILink } from './menus/link'

export interface IProductAttributeValue {
    id: string;
    uri: string;
    name: string;
    slug: string;
    active: boolean;
}

export interface IProductAttribute {
    id: string;
    uri: string;
    name: string;
    slug: string;
    termset?: string;
    values: IProductAttributeValue[];
}

export interface IProductAttributeSelect {
    attributeUri: string;
    valueUri: string;
}

export interface IProduct {
    id: string;
    uri: string;
    slug: string;
    selected?: number | boolean;
    name: string;
    sku: string;
    images: string[];
    price: number;
    compareAtPrice: number | null;
    brand: IBrand | null;
    badges: string[];
    categories: IShopCategory[];
    reviews: number;
    rating: number;
    attributes: IProductAttribute[];
    availability: string;
    description: string | null;
    variants: IProduct[];
    merchant: string | null;
    categoryPath: ILink[];
}

export type IProductsList = IPaginatedList<IProduct> & IFilterableList<IProduct, IFilter>;

