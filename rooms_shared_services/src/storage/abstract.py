from abc import ABC, abstractmethod
from typing import Any


class AbstractStorageClient(ABC):
    @abstractmethod
    def retrieve(self, key: dict[Any, Any], **call_params: Any):
        ...

    @abstractmethod
    def create(self, table_item: dict[Any, Any], **call_params: Any):
        ...

    @abstractmethod
    def update(self, key: dict[Any, Any], attribute_updates: dict[Any, Any], **call_params: Any):
        ...

    @abstractmethod
    def delete(self, key: Any, **call_params: Any):
        ...

    @abstractmethod
    def bulk_retrieve(self, keys: list[dict[Any, Any]], **call_params: Any):
        ...

    @abstractmethod
    def bulk_create(self, table_items: list[dict[Any, Any]], **call_params: Any):
        ...

    @abstractmethod
    def bulk_update(self, keys: list[dict[Any, Any]], attribute_updates_list: list[dict[Any, Any]], **call_params: Any):
        ...

    @abstractmethod
    def bulk_delete(self, keys: list[dict[Any, Any]], **call_params: Any):
        ...
