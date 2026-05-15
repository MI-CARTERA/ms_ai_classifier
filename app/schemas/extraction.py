from pydantic import BaseModel

from app.schemas.classification import NormalizedTransaction, StatementPeriod


class ExtractionResult(BaseModel):
    bank_name: str | None = None
    account_holder: str | None = None
    account_number_last4: str | None = None
    statement_period: StatementPeriod | None = None
    currency: str | None = None
    extracted_text: str
    extraction_summary: str
    transactions: list[NormalizedTransaction]
