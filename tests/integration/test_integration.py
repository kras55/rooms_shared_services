import logging
import socket

import backoff
import boto3
import pytest
from faker import Faker
from mypy_boto3_dynamodb import ServiceResource

from rooms_shared_services.src.storage.dynamodb import DynamodbStorageClient

fake = Faker()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class TestDatabaseConnection:  # noqa: WPS306
    def setup_class(cls):
        logging.basicConfig(level=logging.INFO)
        endpoint_url = "http://dynamodb-local:8000"
        dyn_resource: ServiceResource = boto3.resource("dynamodb", region_name="us-east-1", endpoint_url=endpoint_url)
        cls.key_names = [fake.pystr(), fake.pystr()]
        key_types = ["HASH", "RANGE"]
        cls.keys = [
            {"AttributeName": key_name, "KeyType": arg_type} for key_name, arg_type in zip(cls.key_names, key_types)
        ]
        attributes = [{"AttributeName": fake.pystr(), "AttributeType": arg_type} for arg_type in "SNB"]
        attributes = []
        attributes.extend([{"AttributeName": name, "AttributeType": "S"} for name in cls.key_names])
        provisioned_throughput = {"ReadCapacityUnits": 1, "WriteCapacityUnits": 1}

        logger.info(f"KeySchema: {cls.keys}")
        cls.tablename = fake.pystr()
        cls.table = dyn_resource.create_table(
            AttributeDefinitions=attributes,
            TableName=cls.tablename,
            KeySchema=cls.keys,
            ProvisionedThroughput=provisioned_throughput,
        )
        cls.dynamodb_client = DynamodbStorageClient(tablename=cls.tablename, endpoint_url=endpoint_url)

    @backoff.on_exception(backoff.constant, Exception, max_time=5)
    def test_conn(self):
        port = 8000
        host = "dynamodb-local"
        timeout = 2
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # presumably
        sock.settimeout(timeout)
        try:
            sock.connect((host, port))
        except Exception as err:
            logger.info("Connection failed: {}".format(err))
            raise
        else:
            sock.close()
            logger.info("Connection succeded")

    def test_table(self):
        assert self.table.name == self.tablename

    @pytest.fixture
    def attribute(self):
        return {fake.pystr(): fake.pyint()}

    @pytest.fixture
    def item_key(self):
        return {entry["AttributeName"]: fake.pystr() for entry in self.keys}

    @pytest.fixture
    def table_item(self, attribute, item_key):
        table_item = {}
        table_item.update(item_key)
        table_item.update(attribute)
        return table_item

    @pytest.fixture(autouse=True)
    def clean_table(self):
        init_items = self.table.scan()["Items"]
        assert not init_items
        yield
        res_items = self.table.scan()["Items"]
        for record in res_items:
            key = {key_name: record[key_name] for key_name in self.key_names}
            self.table.delete_item(Key=key)

    @pytest.fixture
    def put_result(self, table_item):
        return self.table.put_item(Item=table_item)

    def test_retrieve(self, attribute, item_key, put_result):
        assert isinstance(put_result, dict)
        result_item = self.dynamodb_client.retrieve(key=item_key)
        assert isinstance(result_item, dict)
        for key in item_key.keys():
            assert item_key[key] == result_item.pop(key)  # noqa: WPS204
        assert result_item == attribute

    def test_create(self, attribute, item_key, table_item):
        self.dynamodb_client.create(table_item=table_item)
        response = self.table.get_item(Key=item_key)
        result_item = response["Item"]
        for key in item_key.keys():
            assert item_key[key] == result_item.pop(key)
        assert result_item == attribute

    def test_update(self, attribute, item_key, put_result):
        attribute_key = list(attribute.keys())[0]
        assert isinstance(put_result, dict)
        update_value = fake.pyint()
        update = {attribute_key: update_value}
        self.dynamodb_client.update(key=item_key, attribute_updates=update)
        response = self.table.get_item(Key=item_key)
        result_item = response["Item"]
        for key in item_key.keys():
            assert item_key[key] == result_item.pop(key)
        assert result_item == update

    def test_delete(self, put_result, item_key):
        assert isinstance(put_result, dict)
        self.dynamodb_client.delete(key=item_key)
        table_items = self.table.scan()["Items"]
        assert not table_items

    def test_bulk_retrieve(self, attribute, item_key, put_result):
        assert isinstance(put_result, dict)
        response = self.dynamodb_client.bulk_retrieve(keys=[item_key])
        assert isinstance(response, list)
        result_item = response[0]
        for key in item_key.keys():
            assert item_key[key] == result_item.pop(key)
        assert result_item == attribute

    def test_bulk_create(self, attribute, item_key, table_item):
        self.dynamodb_client.bulk_create(table_items=[table_item])
        response = self.table.get_item(Key=item_key)
        result_item = response["Item"]
        for key in item_key.keys():
            assert item_key[key] == result_item.pop(key)
        assert result_item == attribute

    def test_bulk_update(self, attribute, item_key, put_result):
        attribute_key = list(attribute.keys())[0]
        assert isinstance(put_result, dict)
        update_value = fake.pyint()
        update = {attribute_key: update_value}
        self.dynamodb_client.bulk_update(keys=[item_key], attribute_updates_list=[update])
        response = self.table.get_item(Key=item_key)
        result_item = response["Item"]
        for key in item_key.keys():
            assert item_key[key] == result_item.pop(key)
        assert result_item == update

    def test_bulk_delete(self, item_key, put_result):
        assert isinstance(put_result, dict)
        self.dynamodb_client.bulk_delete(keys=[item_key])
        scanned_items = self.table.scan()["Items"]
        assert not scanned_items

    def test_pagination(self, attribute, item_key, put_result):
        assert isinstance(put_result, dict)
        for batch in self.dynamodb_client.get_by_pages(filter_params={}):
            assert isinstance(batch, list)
            for result_item in batch:
                logger.info("assert equal:")
                for key in item_key.keys():
                    logger.info(item_key[key])
                    logger.info(result_item[key])
                    logger.info("***")
                    assert item_key[key] == result_item.pop(key)
                assert result_item == attribute
