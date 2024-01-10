import logging
from decimal import Decimal

import boto3
from mypy_boto3_dynamodb.service_resource import Table
from pydantic_settings import BaseSettings

from rooms_shared_services.src.storage.abstract import AbstractStorageClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DynamodbSettings(BaseSettings):
    table: str


class DynamodbStorageClient(AbstractStorageClient):
    def __init__(self, tablename: str, region_name: str = "us-east-1", endpoint_url: str | None = None):
        """Set properties.

        Args:
            tablename (str): _description_
            region_name (str): _description_. Defaults to "us-east-1".
            endpoint_url (str | None, optional): _description_. Defaults to None.
        """
        resource_params = {
            "region_name": region_name,
        }
        if endpoint_url:
            resource_params.update({"endpoint_url": endpoint_url})
        self.table: Table = boto3.resource("dynamodb", **resource_params).Table(tablename)  # type: ignore

    def __call__(self):
        logger.info("Hello world")

    def retrieve(self, key: dict, **call_params) -> dict:
        response = self.table.get_item(Key=key, **call_params)
        return response["Item"]

    def create(self, table_item: dict, **call_params) -> dict:
        return dict(self.table.put_item(Item=table_item, **call_params))

    def update(self, key: dict, attribute_updates: dict, **call_params) -> dict:
        update_expression = "SET "
        expression_attribute_values = {}
        for idx, update in enumerate(attribute_updates.items()):
            value_name = ":val{}".format(idx)
            update_value = update[1]
            update_value = Decimal(str(update_value)) if isinstance(update_value, (int, float)) else update_value
            update_expression = "{} {} = {}".format(update_expression, update[0], value_name)
            expression_attribute_values[value_name] = update_value
        return dict(
            self.table.update_item(
                Key=key,
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values,
                **call_params,
            ),
        )

    def delete(self, key: dict, **call_params) -> dict:
        return dict(self.table.delete_item(Key=key, **call_params))

    def bulk_retrieve(self, keys: list[dict], **call_params) -> list[dict]:
        return [self.retrieve(key=key, **call_params) for key in keys]

    def bulk_create(self, table_items: list[dict], **call_params) -> None:
        with self.table.batch_writer() as batch:
            for table_item in table_items:
                batch.put_item(Item=table_item, **call_params)

    def bulk_update(self, keys: list[dict], attribute_updates_list: list[dict], **call_params) -> list[dict]:
        if len(keys) == len(attribute_updates_list):
            responses = []
            for key, attribute_updates in zip(keys, attribute_updates_list):
                responses.append(self.update(key=key, attribute_updates=attribute_updates, **call_params))
            return responses
        raise ValueError("Keys and attribute_updates_list must be of equal size")

    def bulk_delete(self, keys: list[dict], **call_params) -> None:
        with self.table.batch_writer() as batch:
            for key in keys:
                batch.delete_item(Key=key, **call_params)
