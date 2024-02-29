from datetime import datetime, timezone
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

from rooms_shared_services.src.delayed_tasks.abstract import (
    AbstractDelayedTaskBulkStorageClient,
    AbstractDelayedTaskSingleStorageClient,
)
from rooms_shared_services.src.delayed_tasks.models import DelayedTask, TaskStatus
from rooms_shared_services.src.settings.delayed_tasks import Settings as DelayedTasksSettings
from rooms_shared_services.src.storage.dynamodb import DynamodbStorageClient

delayed_task_settings = DelayedTasksSettings()
dynamodb_resource = boto3.resource("dynamodb", region_name=delayed_task_settings.region_name)


class DynamodbDelayedTaskSingleClient(AbstractDelayedTaskSingleStorageClient):
    def __init__(self, db_client: DynamodbStorageClient, task_id: str, attempt_number: int | None = None):
        """Assign attribues.

        Args:
            db_client (DynamodbStorageClient): _description_
            task_id (str): _description_
            attempt_number (int | None, optional): _description_. Defaults to None.
        """
        self.db_client = db_client
        match attempt_number:
            case None:
                query_resp = self.db_client.table.query(KeyConditionExpression=Key("task_id").eq(task_id))
                task_items = query_resp["Items"]
                task_items.sort(key=self.sort_by_attempt_number)
                task_item = task_items[-1]
            case _:
                get_resp = self.db_client.table.get_item(
                    Key={"task_id": task_id, "attempt_number": Decimal(attempt_number)},
                )
                task_item = get_resp["Item"]
        self.task_item_key = {"task_id": task_item["task_id"], "attempt_number": task_item["attempt_number"]}

    @staticmethod
    def sort_by_attempt_number(attempt):
        return attempt["attempt_number"]

    def retrieve(self):
        return self.db_client.retrieve(key=self.task_item_key)

    def update_status(self, status: TaskStatus):
        attribute_updates = {"task_status": status}
        return self.db_client.update(key=self.task_item_key, attribute_updates=attribute_updates)


class DynamodbDelayedTaskBulkStorageClient(AbstractDelayedTaskBulkStorageClient):
    def __init__(self, db_client: DynamodbStorageClient, task_variant: str) -> None:
        """Assign db_client.

        Args:
            db_client (DynamodbStorageClient): _description_
            task_variant (str): _description_
        """
        self.db_client = db_client
        super().__init__(task_variant=task_variant)

    def get_task_items(self, status: TaskStatus) -> list[DelayedTask]:
        filter_params = {"task_status": status, "task_variant": self.task_variant}
        task_items = self.db_client.bulk_get(filter_params=filter_params)
        return [DelayedTask.model_validate(task_item) for task_item in task_items]

    def bulk_update_status(self, key_list: list[dict], status: TaskStatus) -> list[dict]:
        match status:
            case "scheduled":
                timestamp_attr = "scheduled_at"
            case "pending":
                timestamp_attr = "pending_at"
            case "processing":
                timestamp_attr = "processed_at"
            case "succeded":
                timestamp_attr = "succeded_at"
            case "failed":
                timestamp_attr = "failed_at"
            case _:
                raise ValueError("Invalid task status")
        timestamp = datetime.now(tz=timezone.utc).isoformat()
        attribute_update_list = [{"task_status": status, timestamp_attr: timestamp}] * len(key_list)  # noqa: WPS435
        return self.db_client.bulk_update(keys=key_list, attribute_updates_list=attribute_update_list)
