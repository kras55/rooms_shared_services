import logging
from decimal import Decimal
from typing import Any, Literal

import boto3
from boto3.dynamodb.conditions import Attr
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table
from pydantic_settings import BaseSettings

from rooms_shared_services.src.storage.abstract import AbstractStorageClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ConditionLiteral = Literal["OR", "AND"]


class DynamodbSettings(BaseSettings):
    table: str


class DynamodbStorageClient(AbstractStorageClient):
    def __init__(
        self,
        tablename: str,
        region_name: str = "us-east-1",
        endpoint_url: str | None = None,
        create_table_params: dict | None = None,
    ):
        """Set attributes.Create db table if needed.

        Args:
            tablename (str): _description_
            region_name (str): _description_. Defaults to "us-east-1".
            endpoint_url (str | None): _description_. Defaults to None.
            create_table_params (dict | None): _description_. Defaults to None.
        """
        resource_params = {
            "region_name": region_name,
        }
        if endpoint_url:
            resource_params.update({"endpoint_url": endpoint_url})
        dynamodb_resource: DynamoDBServiceResource = boto3.resource("dynamodb", **resource_params)  # type: ignore
        if create_table_params:
            if "ProvisionedThroughput" not in create_table_params:
                create_table_params.update(
                    {
                        "ProvisionedThroughput": {
                            "ReadCapacityUnits": 5,
                            "WriteCapacityUnits": 5,
                        },
                    },
                )
            dynamodb_resource.create_table(TableName=tablename, **create_table_params)
        self.table: Table = dynamodb_resource.Table(tablename)  # type: ignore

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
        attribute_update_items = attribute_updates.items()
        for idx, update in enumerate(attribute_update_items):
            value_name = ":val{}".format(idx)
            update_value = update[1]
            update_value = Decimal(str(update_value)) if isinstance(update_value, (int, float)) else update_value
            update_expression = "{} {} = {},".format(update_expression, update[0], value_name)
            expression_attribute_values[value_name] = update_value
        update_expression = update_expression[:-1]
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

    def bulk_update(self, keys: list[dict[Any, Any]], attribute_updates_list: list[dict], **call_params) -> list[dict]:
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

    def bulk_get(self, filter_params: dict, condition: ConditionLiteral = "AND"):
        filter_params_list = list(filter_params.items())
        first_params_item = filter_params_list.pop(0)
        FilterExpression = Attr(first_params_item[0]).eq(first_params_item[1])  # noqa: N806
        for next_params_item in filter_params_list:
            match condition:
                case "AND":
                    FilterExpression = FilterExpression & Attr(next_params_item[0]).eq(  # type: ignore # noqa: N806
                        next_params_item[1],
                    )
                case "OR":
                    FilterExpression = FilterExpression | Attr(next_params_item[0]).eq(  # type: ignore # noqa: N806
                        next_params_item[1],
                    )
                case _:
                    raise ValueError("Invalid filter expression condition")
        resp = self.table.scan(FilterExpression=FilterExpression)
        return resp["Items"]
