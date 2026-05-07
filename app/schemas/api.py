from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ClassificationJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: str
    file_id: int
    user_id: int
    bank_account_id: int | None
    status: str
    file_name: str
    storage_path: str
    extracted_text: str | None
    classification_result: dict | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
