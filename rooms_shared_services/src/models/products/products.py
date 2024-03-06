from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl

from rooms_shared_services.src.storage.models import BaseDynamodbModel

UNSET = Literal["UNSET"]


class ProductDescription(BaseModel):
    language_code: str
    full: str | None = None
    short: str | None = None
    translation_provider: str | None = None
    approved: bool | None = None


class ProductBrand(BaseModel):
    id: UUID | None = None
    name: str | None = None
    website: HttpUrl | None = None
    catalog_pdf: HttpUrl | None = None
    description: str | None = None
    logo: HttpUrl | None = None


class ProductCollection(BaseModel):
    id: UUID | None = None
    name: str | None = None
    catalog_pdf: HttpUrl | None = None
    description: str | None = None
    logo: HttpUrl | None = None


class ColorAttributes(BaseModel):
    main_color: str | None = None
    main_color_image: HttpUrl | None = None
    color: str | None = None
    color_image: HttpUrl | None = None
    upholstery_color: str | None = None
    upholstery_color_image: HttpUrl | None = None
    front_color: str | None = None
    front_color_image: HttpUrl | None = None
    cabinet_color: str | None = None
    cabinet_color_image: HttpUrl | None = None


class ImageSet(BaseModel):
    small: HttpUrl | None = None
    medium: HttpUrl | None = None
    large: HttpUrl | None = None


class PackagePack(BaseModel):
    ean: str | None = None
    weight: float | None = None
    length: float | None = None
    packNum: int | None = None  # noqa: N815
    height: float | None = None
    width: float | None = None


class StoreVariantRelatedValues(BaseDynamodbModel):
    default: str | int | datetime


class GeoRelatedValues(BaseDynamodbModel):
    default: StoreVariantRelatedValues
    israel: StoreVariantRelatedValues | None = None
    uk: StoreVariantRelatedValues | None = None


class LanguageRelatedValues(BaseDynamodbModel):
    default: GeoRelatedValues
    hebrew: GeoRelatedValues | None = None
    english: GeoRelatedValues | None = None
    russian: GeoRelatedValues | None = None


class RelatedValues(BaseDynamodbModel):
    wc: LanguageRelatedValues


class ProductItem(BaseDynamodbModel):
    id: UUID = Field(default_factory=uuid4)
    original_ident: str | None | UNSET = UNSET
    ident_code: str | None | UNSET = UNSET
    name: str | None | UNSET = UNSET
    slug: str | None | UNSET = UNSET
    created_at: datetime | None | UNSET = UNSET
    modified_at: datetime | None | UNSET = UNSET
    original_description_full: str | None | UNSET = UNSET
    original_description_short: str | None | UNSET = UNSET
    original_description_language_code: str | None | UNSET = UNSET
    origin_country: str | None | UNSET = UNSET
    pickup_location: str | None | UNSET = UNSET
    pickup_address: str | None | UNSET = UNSET
    shipment_term_code: str | None | UNSET = UNSET
    catalog_pdf: HttpUrl | None | UNSET = UNSET
    pickup_downtime: int | None | UNSET = UNSET
    brand_catalog_pages: list[int] | None | UNSET = UNSET
    collection_catalog_pages: list[int] | None | UNSET = UNSET
    brand_website_links: list[HttpUrl] | None | UNSET = UNSET
    sku: str | None | UNSET = UNSET
    wc_price: RelatedValues | None | UNSET = UNSET
    retail_price: float | None | UNSET = UNSET
    wholesale_price: int | None | UNSET = UNSET
    currency_code: str | None | UNSET = UNSET
    gross_weight: float | None | UNSET = UNSET
    net_weight: float | None | UNSET = UNSET
    height: float | None | UNSET = UNSET
    width: float | None | UNSET = UNSET
    depth: float | None | UNSET = UNSET
    related_ids: list[UUID] | None | UNSET = UNSET
    upsell_ids: list[UUID] | None | UNSET = UNSET
    cross_sell_ids: list[UUID] | None | UNSET = UNSET
    categories: list[str] | None | UNSET = UNSET
    tags: list[str] | None | UNSET = UNSET
    image_sets: list[ImageSet] | None | UNSET = UNSET
    descriptions: list[ProductDescription] | None | UNSET = UNSET
    wc_descriptions: RelatedValues | None | UNSET = UNSET
    color_attributes: ColorAttributes | None | UNSET = UNSET
    brand: ProductBrand | None | UNSET = UNSET
    collection: ProductCollection | None | UNSET = UNSET
    ean_GTIN: str | None | UNSET = UNSET  # noqa: N815
    qty_of_boxes: int | None | UNSET = UNSET
    brand_code: str | None | UNSET = UNSET
    volume_m3: float | None | UNSET = UNSET
    package_packs: list[PackagePack] | None | UNSET = UNSET
    qty_per_box: int | None | UNSET = UNSET
    ean: str | None | UNSET = UNSET
    withdrawn: bool | None | UNSET = UNSET
    pcn: str | None | UNSET = UNSET
    catgories: list[str] | None | UNSET = UNSET
    categories: RelatedValues | None | UNSET = UNSET
    published: RelatedValues | None | UNSET = UNSET
