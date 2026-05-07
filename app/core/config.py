from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="ms_ai_classifier", alias="APP_NAME")
    app_env: Literal["local", "dev", "test", "prod"] = Field(default="local", alias="APP_ENV")
    app_port: int = Field(default=8080, alias="APP_PORT")

    database_url: str = Field(
        default="postgresql+psycopg://ms_ai_classifier:ms_ai_classifier@postgres:5432/ms_ai_classifier",
        alias="DATABASE_URL",
    )
    rabbitmq_url: str = Field(default="amqp://guest:guest@rabbitmq:5672/", alias="RABBITMQ_URL")
    rabbitmq_exchange: str = Field(default="mi_cartera_events", alias="RABBITMQ_EXCHANGE")
    rabbitmq_queue: str = Field(default="ms_ai_classifier_queue", alias="RABBITMQ_QUEUE")
    rabbitmq_routing_keys: str = Field(default="files.file_uploaded", alias="RABBITMQ_ROUTING_KEYS")

    files_base_path: str = Field(default="/data/files", alias="FILES_BASE_PATH")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-5", alias="OPENAI_MODEL")
    openai_max_pdf_pages: int = Field(default=12, alias="OPENAI_MAX_PDF_PAGES")

    files_status_callback_url: str | None = Field(default=None, alias="FILES_STATUS_CALLBACK_URL")
    transactions_status_callback_url: str | None = Field(
        default=None,
        alias="TRANSACTIONS_STATUS_CALLBACK_URL",
    )

    @property
    def rabbitmq_routing_key_list(self) -> list[str]:
        return [value.strip() for value in self.rabbitmq_routing_keys.split(",") if value.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
