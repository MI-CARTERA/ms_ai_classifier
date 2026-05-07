from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EventEnvelope(BaseModel):
    event_name: str
    event_version: int = 1
    event_id: UUID
    occurred_at: datetime
    producer: str
    correlation_id: str | None = None
    causation_id: str | None = None


class FileUploadedPayload(BaseModel):
    file_id: int
    user_id: int
    bank_account_id: int | None = None
    file_name: str
    storage_path: str
    content_type: str
    size: int | None = None
    uploaded_at: datetime
    storage_provider: str | None = None
    statement_hint: str | None = None
    source: str | None = None


class FileUploadedEvent(EventEnvelope):
    payload: FileUploadedPayload
