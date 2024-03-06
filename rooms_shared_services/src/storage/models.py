from decimal import Decimal

from pydantic import BaseModel


class BaseDynamodbModel(BaseModel):
    def convert_value(self, item_value, exclude_unset: bool):
        match item_value:
            case BaseDynamodbModel():
                item_value = item_value.dynamodb_dump(exclude_unset=exclude_unset)
            case int():
                item_value = Decimal(item_value)
            case float():
                item_value = Decimal(str(item_value))
            case dict():
                item_value = self.convert_dict(item_value, exclude_unset=exclude_unset)
            case list():
                item_value = [
                    self.convert_value(item_value_item, exclude_unset=exclude_unset) for item_value_item in item_value
                ]
            case _:
                item_value = str(item_value)
        return item_value

    def convert_dict(self, item_dict: dict, exclude_unset: bool):
        return {
            item_key: self.convert_value(item_value, exclude_unset=exclude_unset)
            for (item_key, item_value) in item_dict.items()
        }

    def dynamodb_dump(self, exclude_unset: bool = True):
        item_dict = self.model_dump(exclude_unset=exclude_unset)
        return self.convert_dict(item_dict=item_dict, exclude_unset=exclude_unset)

    @classmethod
    def validate_dynamodb_item(cls, data_dict: dict):
        key_value_dict = {}
        for product_key, product_value in data_dict.items():
            match product_key:
                case _:
                    key_value_dict.update({product_key: product_value})
        return cls(**key_value_dict)
