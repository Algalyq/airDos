import re

from app.services.parsers.base import BaseParser
from app.services.parsers.ocr import extract_text_from_bytes


class PassportParser(BaseParser):
    def doc_type(self) -> str:
        return "passport"

    def parse(self, file_bytes: bytes, filename: str, content_type: str | None = None) -> dict:
        text = extract_text_from_bytes(file_bytes, content_type, filename)

        return {
            "document_type": "passport",
            "passport_number": self._extract(r"(?:Passport\s*No\.?|СЕРИЯ\s*И\s*НОМЕР)\s*[:\-]?\s*([A-Z]{2}[0-9]{7})", text),
            "surname": self._extract(r"Surname\s*[:\-]?\s*([A-Z]+)", text),
            "given_names": self._extract(r"Given\s*names\s*[:\-]?\s*([A-Z\s]+)", text),
            "nationality": self._extract(r"Nationality\s*[:\-]?\s*([A-Z]+)", text),
            "date_of_birth": self._extract(r"Date\s*of\s*birth\s*[:\-]?\s*([0-9]{2}\.[0-9]{2}\.[0-9]{4})", text),
            "raw_text": text[:2000],
        }

    @staticmethod
    def _extract(pattern: str, text: str) -> str | None:
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else None
