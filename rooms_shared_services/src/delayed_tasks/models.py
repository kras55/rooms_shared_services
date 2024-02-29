from typing import Literal
from uuid import UUID

from rooms_shared_services.src.storage.models import BaseDynamodbModel

TaskStatus = Literal["scheduled", "pending", "processing", "succeded", "failed"]


class DelayedTaskKey(BaseDynamodbModel):
    task_id: UUID
    attempt_number: int


class DelayedTask(BaseDynamodbModel):
    task_id: UUID
    attempt_number: int
    task_variant: str = ""
    scheduled_at: str | None = None
    pending_at: str | None = None
    processed_at: str | None = None
    succeded_at: str | None = None
    failed_at: str | None = None
    task_status: TaskStatus
    task_content: dict

    @property
    def key(self):
        return DelayedTaskKey(task_id=self.task_id, attempt_number=self.attempt_number)
