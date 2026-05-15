import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

import fitz

from app.core.config import settings
from app.schemas.classification import NormalizedTransaction, StatementPeriod
from app.schemas.extraction import ExtractionResult

try:
    import pdfplumber
except ImportError:  # pragma: no cover - optional fallback
    pdfplumber = None


DATE_PREFIX_RE = re.compile(r"^(?P<date>\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?|\d{4}[/-]\d{1,2}[/-]\d{1,2})\s+")
AMOUNT_RE = re.compile(r"-?\(?[$€£]?\d[\d.,]*\)?")
IGNORED_LINE_KEYWORDS = (
    "saldo anterior",
    "saldo final",
    "balance anterior",
    "balance final",
    "página",
    "pagina",
    "page ",
)


class PdfExtractor:
    def __init__(self, max_pages: int) -> None:
        self.max_pages = max_pages

    def resolve_path(self, storage_path: str) -> Path:
        path = Path(storage_path)
        if path.is_absolute():
            return path
        return Path(settings.files_base_path) / storage_path

    def extract(self, storage_path: str) -> ExtractionResult:
        pdf_path = self.resolve_path(storage_path)
        text_chunks = self._extract_text_chunks(pdf_path)
        table_lines = self._extract_table_lines(pdf_path)

        all_lines = [line for chunk in text_chunks for line in chunk.splitlines()] + table_lines
        normalized_transactions = self._normalize_transactions(all_lines)
        if not normalized_transactions:
            raise ValueError("No candidate transactions were extracted from the PDF")

        extracted_text = "\n".join(chunk for chunk in text_chunks if chunk.strip())
        currency = self._detect_currency(extracted_text)
        statement_period = self._detect_statement_period(extracted_text)

        return ExtractionResult(
            statement_period=statement_period,
            currency=currency,
            extracted_text=extracted_text,
            extraction_summary=(
                f"Normalized {len(normalized_transactions)} candidate transactions "
                f"from {len(text_chunks)} text chunks and {len(table_lines)} table rows."
            ),
            transactions=normalized_transactions,
        )

    def _extract_text_chunks(self, pdf_path: Path) -> list[str]:
        with fitz.open(pdf_path) as document:
            chunks: list[str] = []
            for page_index, page in enumerate(document):
                if page_index >= self.max_pages:
                    break
                chunks.append(page.get_text("text"))
        return chunks

    def _extract_table_lines(self, pdf_path: Path) -> list[str]:
        if pdfplumber is None:
            return []

        lines: list[str] = []
        with pdfplumber.open(pdf_path) as pdf:
            for page_index, page in enumerate(pdf.pages):
                if page_index >= self.max_pages:
                    break
                for table in page.extract_tables() or []:
                    for row in table:
                        clean_cells = [cell.strip() for cell in row if cell and cell.strip()]
                        if clean_cells:
                            lines.append(" ".join(clean_cells))
        return lines

    def _normalize_transactions(self, lines: list[str]) -> list[NormalizedTransaction]:
        transactions: list[NormalizedTransaction] = []
        seen_raw: set[str] = set()

        for line in lines:
            cleaned = " ".join(line.split()).strip()
            lower = cleaned.lower()
            if not cleaned or any(keyword in lower for keyword in IGNORED_LINE_KEYWORDS):
                continue

            parsed = self._parse_line(cleaned)
            if parsed is None:
                continue
            if parsed.raw_text in seen_raw:
                continue
            seen_raw.add(parsed.raw_text)
            transactions.append(parsed.model_copy(update={"sequence": len(transactions) + 1}))

        return transactions

    def _parse_line(self, line: str) -> NormalizedTransaction | None:
        date_match = DATE_PREFIX_RE.match(line)
        if date_match is None:
            return None

        date_text = date_match.group("date")
        remainder = line[date_match.end():].strip()
        amount_matches = list(AMOUNT_RE.finditer(remainder))
        if not amount_matches:
            return None

        amount_token = amount_matches[-1].group(0)
        balance_token = amount_matches[-2].group(0) if len(amount_matches) >= 2 else None
        description_end = amount_matches[-2].start() if len(amount_matches) >= 2 else amount_matches[-1].start()
        description = remainder[:description_end].strip(" -")
        if len(description) < 3:
            description = remainder[: amount_matches[-1].start()].strip(" -")
        if len(description) < 3:
            return None

        amount = self._parse_decimal(amount_token)
        if amount is None:
            return None
        balance = self._parse_decimal(balance_token) if balance_token else None
        currency = self._detect_currency(line)

        return NormalizedTransaction(
            sequence=0,
            transaction_date=date_text,
            description=description,
            amount=amount,
            currency=currency,
            balance=balance,
            raw_text=line,
            source="table" if "\t" in line else "text",
        )

    @staticmethod
    def _parse_decimal(value: str | None) -> Decimal | None:
        if value is None:
            return None

        normalized = value.replace("$", "").replace("€", "").replace("£", "").strip()
        normalized = normalized.replace("(", "-").replace(")", "")
        if normalized.count(",") > 0 and normalized.count(".") > 0:
            if normalized.rfind(",") > normalized.rfind("."):
                normalized = normalized.replace(".", "").replace(",", ".")
            else:
                normalized = normalized.replace(",", "")
        elif normalized.count(",") > 0:
            normalized = normalized.replace(".", "").replace(",", ".")
        else:
            normalized = normalized.replace(",", "")

        try:
            return Decimal(normalized)
        except InvalidOperation:
            return None

    @staticmethod
    def _detect_currency(text: str) -> str | None:
        if "$U" in text or "UYU" in text:
            return "UYU"
        if "USD" in text or "US$" in text:
            return "USD"
        if "EUR" in text or "€" in text:
            return "EUR"
        if "$" in text:
            return "UYU"
        return None

    @staticmethod
    def _detect_statement_period(text: str) -> StatementPeriod | None:
        matches = re.findall(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}", text)
        if len(matches) >= 2:
            return StatementPeriod(start_date=matches[0], end_date=matches[-1])
        return None
