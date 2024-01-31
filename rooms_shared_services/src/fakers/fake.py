from random import choice
from typing import Any, Literal, TypeVar, get_args
from uuid import uuid4

from faker import Faker
from pydantic import BaseModel
from pydantic.fields import FieldInfo

fake = Faker()


AnnotationName = Literal["str", "int", "float"]


def get_fake_value(field_info: FieldInfo) -> Any:  # noqa: WPS212
    """Get fake value for a field info based on annotation.

    Args:
        field_info (FieldInfo): pydantic FieldInfo instance

    Raises:
        ValueError: When Invalid FieldInfo provided

    Returns:
        Any: any fake value
    """
    if not field_info.annotation:
        return None
    name = field_info.annotation.__name__
    match name:
        case "str":
            return fake.pystr()
        case "int":
            return fake.pyint()
        case "UUID":
            return uuid4()
        case "Literal":
            return choice(get_args(field_info.annotation))
        case "bool":
            return choice((True, False))
        case _:
            raise ValueError("Invalid field annotation for generating fake value: {}".format(name))


T = TypeVar("T", bound="BaseModel")


def make_fake(model_type: type[T]) -> T:
    """Make fake model instance with arbitrary values.

    Args:
        model_type (type[T]): Any BaseModel subclass instance

    Returns:
        T: created fake model instance
    """
    fields = model_type.model_fields
    value_dict = {}
    for key in fields:
        field_info = fields[key]
        fake_value = get_fake_value(field_info=field_info)
        value_dict.update({key: fake_value})
    return model_type.model_validate(value_dict)
