from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="product_category_source_")

    tablename: str
    source_data_bucket: str
    source_data_object: str
    region_name: str
    id_index: str
