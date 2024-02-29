import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any

import aioboto3
import boto3
from pydantic import BaseModel

from rooms_shared_services.src.delayed_tasks.models import DelayedTask, DelayedTaskKey, TaskStatus
from rooms_shared_services.src.settings.delayed_tasks import Settings as DelayedTasksSettings
from rooms_shared_services.src.storage.dynamodb import DynamodbStorageClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

delayed_task_settings = DelayedTasksSettings()
session = aioboto3.Session()


dynamodb = boto3.resource("dynamodb", region_name=delayed_task_settings.region_name)


class AbstractTaskProcessor(ABC):
    """Process task batch.

    Convert received db items batch to task model batch.
    Register batch tasks as being processed.
    Process obtained task batch.
    Register each completed task as being completed.
    """

    def __init__(self, task_runner: "AbstractDelayedTaskRunner") -> None:
        """Assign attributes.

        Args:
            task_runner (AbstractDelayedTaskRunner): _description_
        """
        self.task_runner = task_runner
        self.scheduled_tasks_sleep_sec = delayed_task_settings.scheduled_tasks_sleep_sec
        self.pending_tasks_sleep_sec = delayed_task_settings.pending_tasks_sleep_sec
        self.processing_tasks_sleep_sec = delayed_task_settings.processing_tasks_sleep_sec
        self.succeded_tasks_sleep_sec = delayed_task_settings.succeded_tasks_sleep_sec
        self.failed_tasks_sleep_sec = delayed_task_settings.failed_tasks_sleep_sec

    async def __call__(self, batch: list[DelayedTask]) -> Any:
        logger.info("Tasks processing started.")
        return await self.run_batch(batch=batch)

    @abstractmethod
    async def run_task(self, task: DelayedTask):
        ...

    @abstractmethod
    async def mark_task_processing(self, task_key: DelayedTaskKey):
        ...

    @abstractmethod
    async def mark_task_success(self, task_key: DelayedTaskKey):
        ...

    @abstractmethod
    async def mark_task_failure(self, task_key: DelayedTaskKey):
        ...

    async def handle_task(self, task: DelayedTask):
        """Run ine task.

        Args:
            task (DelayedTask): _description_

        """
        await self.mark_task_processing(task.key)
        task_result = await self.run_task(task)
        if task_result["success"]:
            await self.mark_task_success(task.key)
        else:
            await self.mark_task_failure(task.key)

    async def run_batch(self, batch: list[DelayedTask]) -> dict:
        """Run all tasks.

        Args:
            batch (list[DelayedTask]): _description_

        Returns:
            dict: _description_
        """
        res = {"exhausted": False, "cancelled": False}
        if not len(batch):
            await asyncio.sleep(0)
            res["exhausted"] = True
            return res
        for task in batch:
            await self.handle_task(task)
        return res


class AbstractQueueTaskTracker(ABC):
    bulk_storage_client: "AbstractDelayedTaskBulkStorageClient"
    task_processor: AbstractTaskProcessor
    _scheduled_tasks_exhausted: bool
    _scheduled_tasks_cancelled: bool
    _expires_at: datetime

    def __init__(
        self,
        bulk_storage_client: "AbstractDelayedTaskBulkStorageClient",
        task_processor: AbstractTaskProcessor,
        expire_in_sec: int = 31536000,  # one year in seconds
    ) -> None:
        """Assign attributes.

        Args:
            bulk_storage_client (AbstractDelayedTaskBulkStorageClient): _description_
            task_processor (AbstractTaskProcessor): _description_
            expire_in_sec (int): _description_. Defaults to 31536000.
        """
        self.bulk_storage_client = bulk_storage_client
        self.task_processor = task_processor
        self._scheduled_tasks_exhausted = False
        self._scheduled_tasks_cancelled = False
        self._expires_at = datetime.now(tz=timezone.utc) + timedelta(seconds=expire_in_sec)

    def __call__(self) -> Any:
        logger.info("Task tracker called")
        return asyncio.run(self.run_all())

    async def handle_scheduled_tasks(self):
        logger.info("handle scheduled tasks")
        scheduled_tasks, key_list = self.bulk_storage_client.get_scheduled_task_items()
        self.bulk_storage_client.bulk_mark_pending(key_list=key_list)
        logger.info("Received {} scheduled tasks".format(len(scheduled_tasks)))
        return await self.task_processor.run_batch(batch=scheduled_tasks)

    @property
    def keep_running_scheduled_tasks(self):
        expired = datetime.now(tz=timezone.utc) > self._expires_at
        exhausted = self._scheduled_tasks_exhausted
        logger.info("expired: {}, exhausted: {}".format(expired, exhausted))
        return not (expired or exhausted)

    async def run_scheduled_tasks_loop(self):
        counter = 0
        while self.keep_running_scheduled_tasks:
            res = await self.handle_scheduled_tasks()
            await asyncio.sleep(delayed_task_settings.scheduled_tasks_interval_sec)
            self._scheduled_tasks_exhausted = res["exhausted"]
            self._scheduled_tasks_cancelled = res["cancelled"]
            counter += 1
        return {"counter": counter}

    async def run_all(self):
        async with asyncio.TaskGroup() as tg:
            scheduled_task_loop = tg.create_task(self.run_scheduled_tasks_loop())
        logger.info(f"Scheduled tasks loop completed now: {scheduled_task_loop.result()}")


class AbstractDelayedTaskRunner(ABC):
    task: BaseModel
    task_result: Any
    timeout_sec: int = 60 * 10
    completed: bool
    error: str | None
    succeded: bool | None

    def __init__(self) -> None:
        """Assign attributes."""
        self.completed = False
        self.error = None
        self.succeded = None

    async def __call__(self, task_task_content: dict) -> Any:
        await self.handle_task(task_task_content=task_task_content)
        if self.succeded:
            return {"success": True, "result": self.task_result}
        return {"success": False, "error": self.error}

    @abstractmethod
    async def run(self, task_task_content: dict):
        ...

    async def handle_task(self, task_task_content: dict):
        try:
            await self.run(task_task_content)
        except ValueError as err:
            self.error = str(err)
            self.succeded = False
            self.completed = True


class AbstractDelayedTaskSingleStorageClient(ABC):
    @abstractmethod
    def __init__(self, task_id: str, attempt_number: int | None = None):
        """Use task_id, attempt_number.

        Args:
            task_id (str): _description_
            attempt_number (int | None, optional): _description_. Defaults to None.
        """
        ...

    @abstractmethod
    def retrieve(self):
        ...

    @abstractmethod
    def update_status(self, status: TaskStatus):
        ...

    def mark_as_pending(self):
        return self.update_status(status="pending")

    def mark_as_failed(self):
        return self.update_status(status="failed")

    def mark_as_processing(self):
        return self.update_status(status="processing")

    def mark_as_scheduled(self):
        return self.update_status(status="scheduled")

    def mark_as_succeded(self):
        return self.update_status(status="succeded")


class DynamodbTableMixin(ABC):
    db_client = DynamodbStorageClient(tablename=delayed_task_settings.dynamodb_tablename, region_name="us-east-1")


class AbstractDelayedTaskBulkStorageClient(ABC):
    def __init__(self, task_variant: str):
        """Assign task variant.

        Args:
            task_variant (str): _description_
        """
        self.task_variant = task_variant

    @abstractmethod
    def get_task_items(self, status: TaskStatus) -> list[DelayedTask]:
        ...

    def get_task_items_with_keys(self, status: TaskStatus) -> tuple[list[DelayedTask], list[dict]]:
        task_items = self.get_task_items(status=status)
        key_list = [task_item.key.dynamodb_dump() for task_item in task_items]
        return task_items, key_list

    def get_scheduled_task_items(self) -> tuple[list[DelayedTask], list[dict]]:
        return self.get_task_items_with_keys(status="scheduled")

    def get_pending_task_items(self) -> tuple[list[DelayedTask], list[dict]]:
        return self.get_task_items_with_keys(status="pending")

    def get_processing_task_items(self) -> tuple[list[DelayedTask], list[dict]]:
        return self.get_task_items_with_keys(status="processing")

    def get_succeded_task_items(self) -> tuple[list[DelayedTask], list[dict]]:
        return self.get_task_items_with_keys(status="succeded")

    def get_failed_task_items(self) -> tuple[list[DelayedTask], list[dict]]:
        return self.get_task_items_with_keys(status="failed")

    @abstractmethod
    def bulk_update_status(self, key_list: list[dict], status: TaskStatus) -> list[dict]:
        ...

    def bulk_mark_processed(self, key_list: list[dict]) -> list[dict]:
        return self.bulk_update_status(key_list=key_list, status="processing")

    def bulk_mark_pending(self, key_list: list[dict]) -> list[dict]:
        return self.bulk_update_status(key_list=key_list, status="pending")
