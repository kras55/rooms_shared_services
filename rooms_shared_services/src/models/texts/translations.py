from typing import Any

from pydantic import field_validator

from rooms_shared_services.src.models.texts.languages import Language
from rooms_shared_services.src.storage.models import BaseDynamodbModel


class TextTranslations(BaseDynamodbModel):
    source: Language = Language.en
    en: str | None = None
    ru: str | None = None
    pl: str | None = None
    he: str | None = None
    it: str | None = None
    de: str | None = None
    fr: str | None = None
    uk: str | None = None

    @field_validator("source", mode="before")
    def coerce_source(cls, item_value: Any):
        print("Item value: {}".format(item_value))
        if isinstance(item_value, str):
            try:
                return getattr(Language, item_value)
            except AttributeError:
                pass
        return item_value
