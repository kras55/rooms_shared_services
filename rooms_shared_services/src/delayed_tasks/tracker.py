from rooms_shared_services.src.delayed_tasks.abstract import AbstractQueueTaskTracker
from rooms_shared_services.src.settings.delayed_tasks import Settings as DelayedTasksSettings

delayed_tasks_settings = DelayedTasksSettings()


class DefaultTaskTracker(AbstractQueueTaskTracker):
    """Track delayed tasks of specified task variant.

    Retrieve table name from settings.

    a. Scheduled tasks.
    Receive from dynamodb table batch by batch.
    Pass to bulk processor batch by batch.
    Sleep for specified time interval.
    Repeat while scheduled tasks exist.

    b. Pending tasks.
    Receive from dynamodb table batch by batch.
    Retrieve overdue tasks.
    Mark overdue tasks as failed.

    c. Processed tasks.
    Receive from dynamodb table batch by batch.
    Retrieve overdue tasks.
    Mark overdue tasks as failed.

    d. Succeded tasks.
    Receive from dynamodb table batch by batch.
    Run success_callback.

    e. Failed tasks.
    Receive from dynamodb table batch by batch.
    Check repeat constraints.
    Schedule a repeated task as a duplicate of the failed task.

    """

    ...
