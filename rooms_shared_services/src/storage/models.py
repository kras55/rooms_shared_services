from decimal import Decimal

from pydantic import BaseModel


class BaseDynamodbModel(BaseModel):
    def convert_value(self, item_value):
        if isinstance(item_value, int):
            item_value = Decimal(item_value)
        elif isinstance(item_value, float):
            item_value = Decimal(str(item_value))
        elif isinstance(item_value, dict):
            item_value = self.convert_dict(item_value)
        else:
            item_value = str(item_value)
        return item_value

    def convert_dict(self, item_dict: dict):
        dict_items = item_dict.items()
        converted_items = [(key, (self.convert_value(item_value))) for key, item_value in dict_items]
        return dict(converted_items)

    def dynamodb_dump(self, exclude_unset: bool = True):
        item_dict = self.model_dump(exclude_unset=exclude_unset)
        return self.convert_dict(item_dict=item_dict)
