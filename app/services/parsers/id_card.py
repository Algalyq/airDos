import re

from app.services.parsers.base import BaseParser
from app.services.parsers.ocr import extract_text_from_bytes


class KzIdParser(BaseParser):
    def doc_type(self) -> str:
        return "kz_id"

    def parse(self, file_bytes: bytes, filename: str, content_type: str | None = None) -> dict:
        text = extract_text_from_bytes(file_bytes, content_type, filename)

        iin = self._extract_iin(text)
        full_name = self._extract(r"(?:Ф\.И\.О\.?|Full\s?name)\s*[:\-]?\s*([А-ЯЁ\sA-Z]+)", text)
        number = self._extract(r"№?\s*([0-9]{9,10})", text)

        return {
            "document_type": "kz_id",
            "iin": iin,
            "full_name": full_name,
            "document_number": number,
            "nationality": "KZ",
            "raw_text": text[:2000],
        }

    @staticmethod
    def _extract(pattern: str, text: str) -> str | None:
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    @staticmethod
    def _extract_iin(text: str) -> str | None:
        match = re.search(r"\b([0-9]{12})\b", text)
        return match.group(1) if match else None
