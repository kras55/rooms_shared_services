from typing import Literal

from rooms_shared_services.src.models.products.categories import ProductCategory
from rooms_shared_services.src.models.texts.languages import Language
from rooms_shared_services.src.settings.product_categories import Settings as ProductCategorySettings
from rooms_shared_services.src.sources.product_categories.provider import CategoryProvider
from rooms_shared_services.src.storage.dynamodb import DynamodbStorageClient
from rooms_shared_services.src.translation.client import TranslationClient

TranslationVariant = Literal["NAME", "DESCRIPTION"]


class ProductCategoryProcessor(object):
    def __init__(self) -> None:
        """Set storage client."""
        self.settings = ProductCategorySettings()
        self.dynamodb_storage_client = DynamodbStorageClient(
            tablename=self.settings.tablename,
            region_name=self.settings.region_name,
        )

    def clean_table(self):
        for batch in self.list_source_by_pages():
            batch_keys = [{"name": cat_item.name} for cat_item in batch]
            print("{} batch keys added to deleete list".format(len(batch)))
            if batch_keys:
                self.dynamodb_storage_client.bulk_delete(keys=batch_keys)

    def create_update_dict(self, cat_model: ProductCategory, translate_attr: str):
        return {translate_attr: getattr(cat_model, translate_attr).dynamodb_dump()}

    def update_source(self, batch: list[ProductCategory], translate_attr: str):
        attribute_updates_list = [
            self.create_update_dict(cat_model=cat_item, translate_attr=translate_attr) for cat_item in batch
        ]
        keys = [{"name": cat_item.name} for cat_item in batch]
        self.dynamodb_storage_client.bulk_update(keys=keys, attribute_updates_list=attribute_updates_list)

    def update_from_provider(self):
        provider = CategoryProvider()
        cat_list = provider()
        self.current_id = None
        for cat_item in cat_list:
            self.current_id = self.find_or_add(cat_item) or self.current_id
        del self.current_id

    def check_item(self, cat_item: tuple[str, str | None], cat_model: ProductCategory):
        if cat_model.parent_name != cat_item[1]:
            raise ValueError(
                "Parent name of {} does not match: {} and {}".format(cat_item[0], cat_model.parent_name, cat_item[1]),
            )

    def add_item(self, cat_item: tuple[str, str | None]):
        item_id = self.get_next_id()
        cat_item_model = ProductCategory(id=item_id, name=cat_item[0])
        if (parent_name := cat_item[1]) is not None:
            cat_item_model.parent_name = parent_name
        if cat_item_model.parent_name:
            parent_cat_data = self.dynamodb_storage_client.retrieve(key={"name": cat_item_model.parent_name})
            parent_cat = ProductCategory.validate_dynamodb_item(parent_cat_data)
            cat_item_model.parent_id = parent_cat.id
        self.dynamodb_storage_client.create(table_item=cat_item_model.dynamodb_dump())
        return item_id

    def retrieve_item(self, item_id: int):
        resp = self.dynamodb_storage_client.retrieve_from_index(
            index_name=self.settings.id_index,
            attr_name="id",
            attr_value=item_id,
        )
        if resp is None:
            return None
        return ProductCategory.validate_dynamodb_item(resp)

    def find_or_add(self, cat_item: tuple[str, str | None]):
        stored_cat_item = self.dynamodb_storage_client.retrieve(key={"name": cat_item[0]})
        if stored_cat_item:
            stored_cat_item_model = ProductCategory.validate_dynamodb_item(stored_cat_item)
            self.check_item(cat_item=cat_item, cat_model=stored_cat_item_model)
            return None
        return self.add_item(cat_item=cat_item)

    def get_next_id(self):
        if self.current_id is None:
            max_id = 0
            for page in self.dynamodb_storage_client.get_by_pages(consistent_read=True):
                for cat_item in page:
                    if (cat_item_id := cat_item["id"]) > max_id:
                        max_id = cat_item_id  # noqa: WPS220
        else:
            max_id = self.current_id
        return max_id + 1

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
                    txt=txt.replace("_", " "),
                )
            else:
                translations = None
            setattr(category_item, attr, translations)

    def list_source_by_pages(self, page_size: int = 100):
        for page in self.dynamodb_storage_client.get_by_pages(page_size=page_size):  # noqa: WPS526
            yield [ProductCategory.validate_dynamodb_item(category_item) for category_item in page]
