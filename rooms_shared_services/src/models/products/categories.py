from typing import Any

from pydantic import HttpUrl, field_validator

from rooms_shared_services.src.models.texts.translations import TextTranslations
from rooms_shared_services.src.storage.models import BaseDynamodbModel


class ProductCategory(BaseDynamodbModel):
    name: str
    id: int
    parent_id: int | None = None
    parent_name: str | None = None
    description: str | None = None
    image: HttpUrl | None = None
    name_translations: TextTranslations | None = None
    description_translations: TextTranslations | None = None

    @field_validator(
        "image",
        mode="before",
    )
    def coerce_image(cls, item_value: Any):
        if isinstance(item_value, dict):
            return item_value.get("image", None)
        return item_value
