from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.schemas.classification import MovementType, NormalizedTransaction


class ClassificationResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    extracted_transaction_id: int
    sequence: int
    transaction_date: str | None
    description: str
    amount: Decimal
    currency: str | None
    balance: Decimal | None
    movement_type: MovementType
    category: str
    confidence: float
    reason: str
    needs_review: bool
    raw_text: str
    source: str
    created_at: datetime


class UserCorrectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    classification_result_id: int
    corrected_movement_type: MovementType
    corrected_category: str
    correction_reason: str | None
    created_at: datetime


class ClassificationJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: str
    file_id: int
    user_id: int
    bank_account_id: int | None
    tenant_id: str | None
    status: str
    file_name: str
    storage_path: str
    classifier_name: str | None
    currency: str | None
    extraction_summary: str | None
    total_transactions: int
    review_required_count: int
    extracted_text: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    extracted_transactions: list[NormalizedTransaction]
    classifications: list[ClassificationResultResponse]
    corrections: list[UserCorrectionResponse]


class UserCorrectionRequest(BaseModel):
    classification_result_id: int
    corrected_movement_type: MovementType
    corrected_category: str
    correction_reason: str | None = None
