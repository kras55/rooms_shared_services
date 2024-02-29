from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    dynamodb_tablename: str = "delayed-tasks-stage"
    region_name: str = "us-east-1"
    task_variant: str = "wc_halmar_product_update"
    scheduled_tasks_timeout_sec: int = 1
    scheduled_tasks_interval_sec: int = 1
    scheduled_tasks_sleep_sec: int = 0
    pending_tasks_timeout_sec: int = 1
    pending_tasks_interval_sec: int = 1
    pending_tasks_sleep_sec: int = 0
    processing_tasks_timeout_sec: int = 1
    processing_tasks_interval_sec: int = 1
    processing_tasks_sleep_sec: int = 0
    succeded_tasks_timeout_sec: int = 1
    succeded_tasks_interval_sec: int = 1
    succeded_tasks_sleep_sec: int = 0
    failed_tasks_timeout_sec: int = 1
    failed_tasks_interval_sec: int = 1
    failed_tasks_sleep_sec: int = 0
