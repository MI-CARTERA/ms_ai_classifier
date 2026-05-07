import base64
from pathlib import Path

from openai import OpenAI

from app.core.config import settings
from app.schemas.classification import ClassificationOutput

SYSTEM_PROMPT = """
You classify bank statement movements for a personal finance system.
Return only the structured schema.

Rules:
- Focus on real posted account movements from the statement.
- Ignore balances, headers, footers, page numbers, and duplicated table rows.
- Use debit for money leaving the account and credit for money entering the account.
- Choose transaction_type from: expense, income, investment, saving, transfer, unknown.
- Keep category concise and business-meaningful.
- Confidence must be between 0 and 1.
""".strip()


class OpenAIStatementClassifier:
    def __init__(self) -> None:
        self._client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    def classify(self, *, pdf_path: Path, extracted_text: str) -> ClassificationOutput:
        if self._client is None:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        with pdf_path.open("rb") as file_handle:
            base64_string = base64.b64encode(file_handle.read()).decode("utf-8")

        response = self._client.responses.parse(
            model=settings.openai_model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_file",
                            "filename": pdf_path.name,
                            "file_data": f"data:application/pdf;base64,{base64_string}",
                        },
                        {
                            "type": "input_text",
                            "text": (
                                "Extract and classify all bank statement movements into the schema. "
                                "Use the PDF as the primary source. The extracted text below is auxiliary context.\n\n"
                                f"{extracted_text[:20000]}"
                            ),
                        },
                    ],
                },
            ],
            text_format=ClassificationOutput,
        )
        return response.output_parsed
