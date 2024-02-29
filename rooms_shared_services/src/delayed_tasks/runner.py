from rooms_shared_services.src.delayed_tasks.abstract import AbstractDelayedTaskRunner


class BasicDelayedTaskSingleRunner(AbstractDelayedTaskRunner):
    async def run(self, task_task_content: dict):
        self.task_result = {"timeout": self.timeout_sec, "task_content": task_task_content}
        if task_task_content.get("must_raise"):
            raise ValueError("Invalid task task_content")
        self.succeded = True
        self.completed = True
