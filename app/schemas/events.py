from datetime import datetime
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class EventEnvelope(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    event_name: str = Field(validation_alias=AliasChoices("event_name", "eventName"))
    event_version: int = Field(default=1, validation_alias=AliasChoices("event_version", "eventVersion"))
    event_id: UUID = Field(validation_alias=AliasChoices("event_id", "eventId"))
    occurred_at: datetime = Field(validation_alias=AliasChoices("occurred_at", "occurredAt"))
    producer: str
    correlation_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("correlation_id", "correlationId"),
    )
    causation_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("causation_id", "causationId"),
    )


class FileUploadedPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    file_id: int = Field(validation_alias=AliasChoices("file_id", "fileId"))
    user_id: int = Field(validation_alias=AliasChoices("user_id", "userId"))
    bank_account_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("bank_account_id", "bankAccountId"),
    )
    tenant_id: str | None = Field(default=None, validation_alias=AliasChoices("tenant_id", "tenantId"))
    file_name: str = Field(validation_alias=AliasChoices("file_name", "fileName"))
    storage_path: str = Field(
        validation_alias=AliasChoices("storage_path", "storagePath", "storage_key", "storageKey")
    )
    content_type: str = Field(validation_alias=AliasChoices("content_type", "contentType"))
    size: int | None = None
    uploaded_at: datetime = Field(validation_alias=AliasChoices("uploaded_at", "uploadedAt"))
    storage_provider: str | None = Field(
        default=None,
        validation_alias=AliasChoices("storage_provider", "storageProvider"),
    )
    statement_hint: str | None = Field(
        default=None,
        validation_alias=AliasChoices("statement_hint", "statementHint"),
    )
    source: str | None = None


class FileUploadedEvent(EventEnvelope):
    payload: FileUploadedPayload
