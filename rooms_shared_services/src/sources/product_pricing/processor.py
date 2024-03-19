from rooms_shared_services.src.models.products.products import ProductSourceItem
from rooms_shared_services.src.settings.product_source import Settings as ProductSourceSettings
from rooms_shared_services.src.storage.dynamodb import DynamodbStorageClient


class PriceProcessor(object):
    def __init__(self, price_owner_code: str, target_price_code: str) -> None:
        """Set attributes.

        Args:
            price_owner_code (str): _description_
            target_price_code (str): _description_
        """
        product_source_settings = ProductSourceSettings()
        self.dynamodb_storage_client = DynamodbStorageClient(
            tablename=product_source_settings.tablename,
            region_name=product_source_settings.region_name,
        )

        self.price_owner_code = price_owner_code
        self.target_price_code = target_price_code

    def run_all(self):
        for page in self.dynamodb_storage_client.get_by_pages(consistent_read=True):
            product_items = [ProductSourceItem.validate_dynamodb_item(data_item) for data_item in page]
            self.process_page(product_items)

    def process_page(self, item_list: list[ProductSourceItem]):
        ...
