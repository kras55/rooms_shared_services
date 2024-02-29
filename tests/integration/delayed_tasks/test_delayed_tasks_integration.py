import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from faker import Faker

from rooms_shared_services.src.delayed_tasks.models import DelayedTask
from rooms_shared_services.src.delayed_tasks.processor import DynamodbTaskProcessor
from rooms_shared_services.src.delayed_tasks.runner import BasicDelayedTaskSingleRunner
from rooms_shared_services.src.delayed_tasks.storage import (
    DynamodbDelayedTaskBulkStorageClient,
    DynamodbDelayedTaskSingleClient,
)
from rooms_shared_services.src.delayed_tasks.tracker import DefaultTaskTracker
from rooms_shared_services.src.storage.dynamodb import DynamodbStorageClient

fake = Faker()


@pytest.fixture
def task_variant():
    return fake.pystr()


@pytest.fixture
def batch(task_variant):
    models = []
    for _ in range(100):
        model = DelayedTask(
            task_id=uuid4(),
            attempt_number=0,
            scheduled_at=datetime.now(tz=timezone.utc).isoformat(),
            task_status="scheduled",
            task_content={"param_a": 1},
            task_variant=task_variant,
        )
        models.append(model)
    return models


@pytest.fixture
def db_client():
    tablename = fake.pystr()
    endpoint_url = "http://dynamodb-local:8000"
    KeySchema = [
        {"AttributeName": "task_id", "KeyType": "HASH"},  # Partition key
        {"AttributeName": "attempt_number", "KeyType": "RANGE"},  # Sort key
    ]
    AttributeDefinitions = [
        {
            "AttributeName": "task_id",
            "AttributeType": "S",
        },
        {
            "AttributeName": "attempt_number",
            "AttributeType": "N",
        },
    ]
    create_table_params = {"KeySchema": KeySchema, "AttributeDefinitions": AttributeDefinitions}

    return DynamodbStorageClient(
        tablename=tablename, endpoint_url=endpoint_url, create_table_params=create_table_params
    )


@pytest.fixture
def task_runner():
    return BasicDelayedTaskSingleRunner()


@pytest.fixture
def task_processor(db_client, task_runner):
    return DynamodbTaskProcessor(db_client=db_client, task_runner=task_runner)


@pytest.fixture
def db_items(batch: list[DelayedTask], db_client):
    table_items = [task_item.dynamodb_dump(exclude_unset=False) for task_item in batch]
    db_client.bulk_create(table_items=table_items)


@pytest.fixture
def task_tracker(db_client, task_variant, task_processor):
    bulk_storage_client = DynamodbDelayedTaskBulkStorageClient(db_client=db_client, task_variant=task_variant)
    return DefaultTaskTracker(bulk_storage_client=bulk_storage_client, task_processor=task_processor)


@pytest.mark.asyncio
async def test_delayed_task_processor(task_processor, db_items, db_client, batch: list[DelayedTask]):
    await task_processor.run_batch(batch=batch)
    keys = [json.loads(task_item.key.model_dump_json()) for task_item in batch]
    succeded_tasks = db_client.bulk_retrieve(keys=keys)
    assert all([task["task_status"] == "succeded" for task in succeded_tasks])


def test_scheduled_task_tracker(task_tracker, batch, db_client, db_items):
    task_tracker()
    keys = [json.loads(task_item.key.model_dump_json()) for task_item in batch]
    succeded_tasks = db_client.bulk_retrieve(keys=keys)
    assert all([task["task_status"] == "succeded" for task in succeded_tasks])
