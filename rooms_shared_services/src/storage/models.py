from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel


class BaseDynamodbModel(BaseModel):
    def convert_value(self, item_value, exclude_unset: bool):
        match item_value:
            case BaseDynamodbModel():
                converted_item_value = item_value.dynamodb_dump(exclude_unset=exclude_unset)
            case int():
                converted_item_value = Decimal(item_value)
            case float():
                converted_item_value = Decimal(str(item_value))
            case dict():
                converted_item_value = self.convert_dict(item_value, exclude_unset=exclude_unset)
            case list():
                converted_item_value = [
                    self.convert_value(item_value_item, exclude_unset=exclude_unset) for item_value_item in item_value
                ]
            case Enum():
                converted_item_value = item_value.name
            case _:
                converted_item_value = str(item_value)
        return converted_item_value

    def convert_dict(self, item_dict: dict, exclude_unset: bool):
        return {
            item_key: self.convert_value(item_value, exclude_unset=exclude_unset)
            for (item_key, item_value) in item_dict.items()
        }

    def dynamodb_dump(self, exclude_unset: bool = True):
        item_dict = self.model_dump(exclude_unset=exclude_unset)
        return self.convert_dict(item_dict=item_dict, exclude_unset=exclude_unset)

    @classmethod
    def validate_value(cls, item_value: Any) -> Any:
        match item_value:
            case list():
                validated_value = [cls.validate_value(item_value=product_elem) for product_elem in item_value]
            case "None":
                validated_value = None
            case dict():
                return {
                    elem_key: cls.validate_value(item_value=elem_value) for elem_key, elem_value in item_value.items()
                }
            case _:
                validated_value = item_value
        return validated_value

    @classmethod
    def validate_dynamodb_item(cls, data_dict: dict):
        key_value_dict = {}
        for product_key, product_value in data_dict.items():
            validated_key = product_key
            match product_key:
                case _:
                    pass
            validated_value = cls.validate_value(item_value=product_value)
            key_value_dict.update({validated_key: validated_value})

        return cls.model_validate(key_value_dict)
