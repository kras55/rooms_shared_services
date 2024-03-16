import logging
from decimal import Decimal
from typing import Any, Literal

import boto3
from boto3.dynamodb.conditions import Attr, Key
from mypy_boto3_dynamodb import DynamoDBClient
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table
from pydantic_settings import BaseSettings

from rooms_shared_services.src.exceptions.storage import MoreThanOneItemFound
from rooms_shared_services.src.storage.abstract import AbstractStorageClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ConditionLiteral = Literal["OR", "AND"]
FilterAttrCondition = Literal[
    "attribute_type",
    "begins_with",
    "between",
    "contains",
    "eq",
    "exists",
    "gt",
    "gte",
    "is_in",
    "lt",
    "lte",
    "ne",
    "not_exists",
    "size",
]


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
        self.client: DynamoDBClient = boto3.client("dynamodb", **resource_params)

    def __call__(self):
        logger.info("Hello world")

    def retrieve(self, key: dict, **call_params) -> dict:
        response = self.table.get_item(Key=key, **call_params)
        try:
            return response["Item"]
        except KeyError:
            return None

    def index_query(self, index_name: str, attr_name: str, attr_value: str, **call_params) -> dict:
        key_condition_expression = Key(attr_name).eq(attr_value)
        return self.table.query(IndexName=index_name, KeyConditionExpression=key_condition_expression)

    def retrieve_from_index(self, index_name: str, attr_name: str, attr_value: str, **call_params):
        resp = self.index_query(index_name=index_name, attr_name=attr_name, attr_value=attr_value, **call_params)
        match resp["Count"]:
            case 1:
                return resp["Items"][0]
            case 0:
                return None
            case _:
                raise MoreThanOneItemFound

    def list_from_index(self, index_name: str, attr_name: str, attr_value: str, **call_params):
        resp = self.index_query(index_name=index_name, attr_name=attr_name, attr_value=attr_value, **call_params)
        match resp["Count"]:
            case 0:
                return []
            case _:
                return resp["Items"]

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
        print(
            "update item: key {}, UpadteExspression {}, ExpressionAttributeValues {}".format(
                key,
                update_expression,
                expression_attribute_values,
            ),
        )
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

    def bulk_get(
        self,
        filter_params: dict | None = None,
        condition: ConditionLiteral = "AND",
        filter_attr_condition: FilterAttrCondition = "eq",
        negate: bool = False,
    ):
        scan_params = self.create_scan_params(
            filter_params=filter_params,
            condition=condition,
            filter_attr_condition=filter_attr_condition,
            negate=negate,
        )
        resp = self.table.scan(**scan_params)
        return resp["Items"]

    def create_scan_params(
        self,
        filter_attr_condition: FilterAttrCondition,
        condition: ConditionLiteral,
        negate: bool,
        filter_params: dict | None = None,
    ):
        scan_params = {}
        if filter_params:
            FilterExpression = self.create_filter_expression(  # noqa: N806
                filter_params=filter_params,
                filter_attr_condition=filter_attr_condition,
                condition=condition,
                negate=negate,
            )  # noqa: N806
            scan_params.update({"FilterExpression": FilterExpression})
        return scan_params

    def create_filter_expression(
        self,
        filter_params: dict,
        filter_attr_condition: FilterAttrCondition,
        condition: ConditionLiteral,
        negate: bool = False,
    ):
        filter_params_list = list(filter_params.items())
        first_params_item = filter_params_list.pop(0)
        attr_method = getattr(Attr(first_params_item[0]), filter_attr_condition)
        FilterExpression = attr_method(first_params_item[1])  # noqa: N806
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
        if negate:
            FilterExpression = ~(FilterExpression)  # noqa: N806
        return FilterExpression

    def validate_data_elem(self, data_elem_value: dict) -> str | int | float | dict | list | None:
        data_type = list(data_elem_value.keys())[0]
        parsed_value = data_elem_value[data_type]
        validated_value: str | int | float | dict | list | None
        match data_type:
            case "S":
                assert isinstance(parsed_value, str)
                validated_value = parsed_value
                if validated_value == "None":
                    validated_value = None
            case "N":
                assert isinstance(parsed_value, str)
                if "." in parsed_value:
                    validated_value = float(parsed_value)
                else:
                    validated_value = int(parsed_value)
            case "BOOL":
                match parsed_value:
                    case "false":
                        validated_value = False  # noqa: WPS220
                    case "true":
                        validated_value = True  # noqa: WPS220
                    case _:
                        raise ValueError("invalid boolean")  # noqa: WPS220
            case "NULL":
                validated_value = None
            case "M":
                assert isinstance(parsed_value, dict)
                validated_value = {
                    elem_key: self.validate_data_elem(elem_value) for elem_key, elem_value in parsed_value.items()
                }
            case "L":
                validated_value = [self.validate_data_elem(elem_item) for elem_item in parsed_value]
        return validated_value

    def parse_annotated_response(self, data_item: dict):
        return {
            data_elem_key: self.validate_data_elem(data_elem_value)
            for data_elem_key, data_elem_value in data_item.items()
        }

    def get_by_pages(self, page_size: int | None = 100, consistent_read: bool = False):
        paginator = self.client.get_paginator("scan")
        scan_params = {"TableName": self.table.name}
        if page_size:
            scan_params.update({"PaginationConfig": {"PageSize": page_size}})
        for page in paginator.paginate(**scan_params, ConsistentRead=consistent_read):
            table_items = page["Items"]
            logger.info("Collected {} page items from dynamodb table {}".format(len(table_items), self.table.name))
            yield [self.parse_annotated_response(db_item) for db_item in table_items]
