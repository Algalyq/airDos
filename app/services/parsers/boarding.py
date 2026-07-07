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
            "flight_number": self._extract_flight(text),
            "passenger_name": self._extract_passenger(text),
            "departure": self._extract_departure(text),
            "arrival": self._extract_arrival(text),
            "seat": self._extract_seat(text),
            "raw_text": text[:2000],
        }

    @staticmethod
    def _extract(pattern: str, text: str, group: int = 1) -> str | None:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if not match:
            return None
        value = match.group(group).strip()
        return value if value else None

    def _extract_flight(self, text: str) -> str | None:
        patterns = [
            r"(?:Рейс|рейс|Flight|flight|Номер\s*рейса|Flight\s*number)\s*[:\-/\s]*([A-Z]{1,3}\s*\d{2,4})",
            r"\b([A-Z]{2,3}\s*\d{2,4})\b",
        ]
        for pattern in patterns:
            value = self._extract(pattern, text)
            if value:
                return re.sub(r"\s+", "", value).upper()
        return None

    def _extract_passenger(self, text: str) -> str | None:
        patterns = [
            r"(?:Пассажир|Passenger|Жолаушы)\s*[:\-/\s]*([А-ЯЁA-Z][а-яёa-z]+\s*[А-ЯЁA-Z][а-яёa-z]+)",
            r"(?:Ф\.И\.О\.?|ФИО)\s*[:\-/\s]*([А-ЯЁA-Z][а-яёa-z]+\s+[А-ЯЁA-Z][а-яёa-z]+)",
        ]
        for pattern in patterns:
            value = self._extract(pattern, text)
            if value:
                return value
        return None

    def _extract_departure(self, text: str) -> str | None:
        patterns = [
            r"(?:Аэропорт\s*вылета|Departure\s*airport|Вылет|From)\s*[:\-/\s]*.*?\(([A-Z]{3})\)",
            r"(?:Аэропорт\s*вылета|Departure\s*airport)\s*[:\-/\s]*([A-Z]{3})",
        ]
        for pattern in patterns:
            value = self._extract(pattern, text)
            if value:
                return value.upper()
        return self._first_airport(text)

    def _extract_arrival(self, text: str) -> str | None:
        patterns = [
            r"(?:Аэропорт\s*прилета|Arrival\s*airport|Прилет|To)\s*[:\-/\s]*.*?\(([A-Z]{3})\)",
            r"(?:Аэропорт\s*прилета|Arrival\s*airport)\s*[:\-/\s]*([A-Z]{3})",
        ]
        for pattern in patterns:
            value = self._extract(pattern, text)
            if value:
                return value.upper()
        return self._second_airport(text)

    def _extract_seat(self, text: str) -> str | None:
        match = re.search(r"(?:Seat|Место)\s*[:\-/\s]*([0-9]{1,3}[A-F])", text, re.IGNORECASE)
        return match.group(1).strip().upper() if match else None

    def _first_airport(self, text: str) -> str | None:
        codes = re.findall(r"\(([A-Z]{3})\)", text)
        return codes[0].upper() if codes else None

    def _second_airport(self, text: str) -> str | None:
        codes = re.findall(r"\(([A-Z]{3})\)", text)
        return codes[1].upper() if len(codes) > 1 else None
