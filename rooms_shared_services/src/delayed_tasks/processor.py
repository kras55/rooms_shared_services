import logging
from asyncio import sleep
from uuid import UUID

from rooms_shared_services.src.delayed_tasks.abstract import AbstractDelayedTaskRunner, AbstractTaskProcessor
from rooms_shared_services.src.delayed_tasks.models import DelayedTask, DelayedTaskKey
from rooms_shared_services.src.delayed_tasks.storage import DynamodbDelayedTaskSingleClient
from rooms_shared_services.src.storage.dynamodb import DynamodbStorageClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DynamodbTaskProcessor(AbstractTaskProcessor):
    def __init__(self, db_client: DynamodbStorageClient, task_runner: AbstractDelayedTaskRunner) -> None:
        """Assign db_client.

        Args:
            db_client (DynamodbStorageClient): _description_
            task_runner (AbstractDelayedTaskRunner): _description_
        """
        self.db_client = db_client
        super().__init__(task_runner)

    @staticmethod
    async def success_callback(task_id: UUID, attempt_number: int):
        await sleep(0)
        logger.info("Success callback for task {}, attempt number {}".format(task_id, attempt_number))

    async def run_task(self, task: DelayedTask):
        await sleep(self.scheduled_tasks_sleep_sec)
        task_result = await self.task_runner(task.task_content)
        logger.info("Processed task: {}. Result: {}".format(task.task_content, task_result))
        return task_result

    async def mark_task_processing(self, task_key: DelayedTaskKey):
        storage_client = DynamodbDelayedTaskSingleClient(
            db_client=self.db_client,
            task_id=str(task_key.task_id),
            attempt_number=task_key.attempt_number,
        )
        storage_client.mark_as_processing()
        await sleep(0)

    async def mark_task_success(self, task_key: DelayedTaskKey):
        storage_client = DynamodbDelayedTaskSingleClient(
            db_client=self.db_client,
            task_id=str(task_key.task_id),
            attempt_number=task_key.attempt_number,
        )
        storage_client.mark_as_succeded()
        await sleep(0)

    async def mark_task_failure(self, task_key: DelayedTaskKey):
        storage_client = DynamodbDelayedTaskSingleClient(
            db_client=self.db_client,
            task_id=str(task_key.task_id),
            attempt_number=task_key.attempt_number,
        )
        storage_client.mark_as_failed()
        await sleep(0)
