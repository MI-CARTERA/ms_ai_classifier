import json

from openai import OpenAI

from app.core.config import settings
from app.schemas.classification import (
    ClassificationDecisionsOutput,
    ClassifiedMovement,
    NormalizedTransaction,
    StatementClassificationResult,
)
from app.schemas.extraction import ExtractionResult

SYSTEM_PROMPT = """
You classify already-extracted bank statement transactions for a personal finance system.
Do not extract new rows. Classify only the provided normalized transactions.

Rules:
- movement_type must be one of: expense, income, transfer, investment, saving, fee, tax, loan_payment, unknown
- category must be concise and useful for personal finance
- confidence must be between 0 and 1
- reason must briefly explain the decision based on description, amount, and context
- If the transaction is ambiguous, use unknown and low confidence
""".strip()


class OpenAIStatementClassifier:
    def __init__(self) -> None:
        self._client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    @property
    def classifier_name(self) -> str:
        return f"openai:{settings.openai_model}"

    def classify(
        self,
        *,
        extraction: ExtractionResult,
        file_name: str,
        statement_hint: str | None,
    ) -> StatementClassificationResult:
        if self._client is None:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        classifications = self._classify_transactions(
            transactions=extraction.transactions,
            context={
                "file_name": file_name,
                "statement_hint": statement_hint,
                "currency": extraction.currency,
                "statement_period": extraction.statement_period.model_dump() if extraction.statement_period else None,
            },
        )

        decisions_by_sequence = {item.sequence: item for item in classifications.classifications}
        merged: list[ClassifiedMovement] = []
        for transaction in extraction.transactions:
            decision = decisions_by_sequence.get(transaction.sequence)
            if decision is None:
                merged.append(
                    ClassifiedMovement(
                        sequence=transaction.sequence,
                        transaction_date=transaction.transaction_date,
                        description=transaction.description,
                        amount=transaction.amount,
                        currency=transaction.currency,
                        balance=transaction.balance,
                        movement_type="unknown",
                        category="needs_review",
                        confidence=0.0,
                        reason="No classification decision was returned for this transaction.",
                        needs_review=True,
                        raw_text=transaction.raw_text,
                        source=transaction.source,
                    )
                )
                continue

            merged.append(
                ClassifiedMovement(
                    sequence=transaction.sequence,
                    transaction_date=transaction.transaction_date,
                    description=transaction.description,
                    amount=transaction.amount,
                    currency=transaction.currency,
                    balance=transaction.balance,
                    movement_type=decision.movement_type,
                    category=decision.category,
                    confidence=decision.confidence,
                    reason=decision.reason,
                    needs_review=decision.confidence < settings.classification_review_threshold,
                    raw_text=transaction.raw_text,
                    source=transaction.source,
                )
            )

        return StatementClassificationResult(
            statement_period=extraction.statement_period,
            currency=extraction.currency,
            extraction_summary=extraction.extraction_summary,
            transactions=merged,
        )

    def _classify_transactions(
        self,
        *,
        transactions: list[NormalizedTransaction],
        context: dict,
    ) -> ClassificationDecisionsOutput:
        transaction_payload = [transaction.model_dump(mode="json") for transaction in transactions]
        response = self._client.responses.parse(
            model=settings.openai_model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "Context:\n"
                                f"{json.dumps(context, ensure_ascii=True)}\n\n"
                                "Transactions:\n"
                                f"{json.dumps(transaction_payload, ensure_ascii=True)}"
                            ),
                        }
                    ],
                },
            ],
            text_format=ClassificationDecisionsOutput,
        )
        return response.output_parsed
