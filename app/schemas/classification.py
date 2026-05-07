from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class StatementPeriod(BaseModel):
    start_date: str | None = None
    end_date: str | None = None


class ClassifiedMovement(BaseModel):
    transaction_date: str | None = None
    description: str
    amount: Decimal
    direction: Literal["debit", "credit"]
    transaction_type: Literal["expense", "income", "investment", "saving", "transfer", "unknown"]
    category: str
    confidence: float = Field(ge=0.0, le=1.0)
    currency: str | None = None
    counterparty: str | None = None
    raw_text: str | None = None
    notes: str | None = None


class ClassificationOutput(BaseModel):
    bank_name: str | None = None
    account_holder: str | None = None
    account_number_last4: str | None = None
    statement_period: StatementPeriod | None = None
    currency: str | None = None
    transactions: list[ClassifiedMovement]
    extraction_summary: str | None = None
