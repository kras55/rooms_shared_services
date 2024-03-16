from typing import Generator, Literal

from rooms_shared_services.src.models.products.categories import ProductCategory
from rooms_shared_services.src.models.texts.languages import Language
from rooms_shared_services.src.storage.dynamodb import DynamodbStorageClient
from rooms_shared_services.src.translation.client import TranslationClient

TranslationVariant = Literal["NAME", "DESCRIPTION"]


class SourceProcessor(object):
    def __init__(self, storage_client: DynamodbStorageClient) -> None:
        """Set storage client.

        Args:
            storage_client (DynamodbStorageClient): _description_
        """
        self.dynamodb_storage_client = storage_client

    def run_all_translation(
        self,
        translation_client: TranslationClient,
        variant: TranslationVariant,
        languages: list[Language] | None = None,
    ):
        languages = languages or list(Language)
        for batch in self.list_source_by_pages(page_size=100):
            match variant:
                case "NAME":
                    attr = "name_translations"
                case "DESCRIPTION":
                    attr = "description_translations"
                case _:
                    raise ValueError("Invalid translation variant.")
            self.run_batch_translation(
                batch=batch,
                translation_client=translation_client,
                languages=languages,
                variant=variant,
                attr=attr,
            )
            self.update_source(batch, translate_attr=attr)
            print("Completed translations")
            for cat_item in batch:
                print(cat_item.name_translations)

    def create_update_dict(self, cat_model: ProductCategory, translate_attr: str):
        return {translate_attr: getattr(cat_model, translate_attr).dynamodb_dump()}

    def update_source(self, batch: list[ProductCategory], translate_attr: str):
        attribute_updates_list = [
            self.create_update_dict(cat_model=cat_item, translate_attr=translate_attr) for cat_item in batch
        ]
        keys = [{"id": cat_item.id} for cat_item in batch]
        self.dynamodb_storage_client.bulk_update(keys=keys, attribute_updates_list=attribute_updates_list)

    def run_batch_translation(  # noqa: WPS211
        self,
        translation_client: TranslationClient,
        variant: TranslationVariant,
        batch: list[ProductCategory],
        languages: list[Language],
        attr: str,
    ):
        for category_item in batch:
            match variant:
                case "NAME":
                    txt = category_item.name
                case "DESCRIPTION":
                    txt = category_item.description
                case _:
                    raise ValueError("Invalid translation variant.")
            if txt:
                translations = translation_client.bulk_translate(
                    source_language=Language.en,
                    target_languages=languages,
                    txt=txt,
                )
            else:
                translations = None
            setattr(category_item, attr, translations)

    def clean_table(self):
        all_keys = []
        for batch in self.list_source_by_pages():
            all_keys.extend([{"id": cat_item.id} for cat_item in batch])
        if all_keys:
            self.dynamodb_storage_client.bulk_delete(keys=all_keys)

    def create_source(self, batch_generator: Generator[list[ProductCategory], None, None]):
        self.clean_table()
        for batch in batch_generator():
            table_items = [category_item.dynamodb_dump(exclude_unset=True) for category_item in batch]
            self.dynamodb_storage_client.bulk_create(table_items=table_items)

    def retrieve_source(self, name: str):
        key = {"name": name}
        category_item = self.dynamodb_storage_client.retrieve(key=key)
        return ProductCategory.validate_dynamodb_item(category_item)

    def list_source_by_pages(self, page_size: int = 100):
        for page in self.dynamodb_storage_client.get_by_pages(page_size=page_size):  # noqa: WPS526
            yield [ProductCategory.validate_dynamodb_item(category_item) for category_item in page]
