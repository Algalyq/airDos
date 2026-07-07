import re

from app.services.parsers.base import BaseParser
from app.services.parsers.ocr import extract_text_from_bytes


class BoardingPassParser(BaseParser):
    def doc_type(self) -> str:
        return "boarding_pass"

    def parse(self, file_bytes: bytes, filename: str, content_type: str | None = None) -> dict:
        text = extract_text_from_bytes(file_bytes, content_type, filename)

        return {
            "document_type": "boarding_pass",
            "flight_number": self._extract(r"Flight\s*[:\-]?\s*([A-Z0-9]{2,8})", text),
            "passenger_name": self._extract(r"Passenger\s*[:\-]?\s*([A-Z\s/]+)", text),
            "departure": self._extract(r"From\s*[:\-]?\s*([A-Z]{3})", text),
            "arrival": self._extract(r"To\s*[:\-]?\s*([A-Z]{3})", text),
            "seat": self._extract(r"Seat\s*[:\-]?\s*([0-9]{1,3}[A-F])", text),
            "raw_text": text[:2000],
        }

    @staticmethod
    def _extract(pattern: str, text: str) -> str | None:
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else None
