from pathlib import Path

import fitz

from app.core.config import settings


class PdfExtractor:
    def __init__(self, max_pages: int) -> None:
        self.max_pages = max_pages

    def resolve_path(self, storage_path: str) -> Path:
        path = Path(storage_path)
        if path.is_absolute():
            return path
        return Path(settings.files_base_path) / storage_path

    def extract_text(self, storage_path: str) -> tuple[Path, str]:
        pdf_path = self.resolve_path(storage_path)
        with fitz.open(pdf_path) as document:
            chunks: list[str] = []
            for page_index, page in enumerate(document):
                if page_index >= self.max_pages:
                    break
                chunks.append(page.get_text("text"))
        return pdf_path, "\n".join(chunk for chunk in chunks if chunk.strip())
