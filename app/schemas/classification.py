from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

MovementType = Literal[
    "expense",
    "income",
    "transfer",
    "investment",
    "saving",
    "fee",
    "tax",
    "loan_payment",
    "unknown",
]


class StatementPeriod(BaseModel):
    start_date: str | None = None
    end_date: str | None = None


class NormalizedTransaction(BaseModel):
    sequence: int
    transaction_date: str | None = None
    description: str
    amount: Decimal
    currency: str | None = None
    balance: Decimal | None = None
    raw_text: str
    source: Literal["text", "table"] = "text"


class ClassificationDecision(BaseModel):
    sequence: int
    movement_type: MovementType
    category: str
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str


class ClassificationDecisionsOutput(BaseModel):
    classifications: list[ClassificationDecision]


class ClassifiedMovement(BaseModel):
    sequence: int
    transaction_date: str | None = None
    description: str
    amount: Decimal
    currency: str | None = None
    balance: Decimal | None = None
    movement_type: MovementType
    category: str
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    needs_review: bool
    raw_text: str
    source: Literal["text", "table"] = "text"


class StatementClassificationResult(BaseModel):
    bank_name: str | None = None
    account_holder: str | None = None
    account_number_last4: str | None = None
    statement_period: StatementPeriod | None = None
    currency: str | None = None
    extraction_summary: str | None = None
    transactions: list[ClassifiedMovement]
