import pytest
from pydantic import BaseModel

from rooms_shared_services.src.fakers.fake import make_fake


@pytest.fixture
def model_type():
    """Define model type.

    Returns:
        _type_: _description_
    """

    class SampleModel(BaseModel):  # noqa: WPS431
        a: int
        b: str

    return SampleModel


def test_fake_model(model_type: type[BaseModel]):  # noqa: D103,WPS442
    fake_data = make_fake(model_type=model_type)
    assert isinstance(fake_data, model_type)
