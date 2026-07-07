import re

from app.services.parsers.base import BaseParser
from app.services.parsers.ocr import extract_text_from_bytes

CITY_TO_IATA = {
    "астана": "NQZ",
    "алматы": "ALA",
    "шымкент": "CIT",
    "актобе": "AKX",
    "атырау": "GUW",
    "орал": "URA",
    "павлодар": "PWQ",
    "караганда": "KGF",
    "тараз": "DMB",
    "костанай": "KSN",
    " nursultan": "NQZ",
    "nur-sultan": "NQZ",
}


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
    def _extract(pattern: str, text: str, group: int = 1, flags: int = re.IGNORECASE | re.MULTILINE) -> str | None:
        match = re.search(pattern, text, flags)
        if not match:
            return None
        value = match.group(group).strip()
        return value if value else None

    def _extract_flight(self, text: str) -> str | None:
        patterns = [
            r"(?:Рейс|рейс|Номер\s*рейса|Flight\s*number|Flight)\s*[:\-/\s.]*([A-Z]{2,3}\s*\d{2,4})",
            r"(?:SCAT|СКАТ|airline|авиакомпания).*?\b([A-Z]{2}\s*\d{3,4})\b",
            r"\b([A-Z]{2}\s*\d{3,4})\b",
        ]
        for pattern in patterns:
            value = self._extract(pattern, text, flags=re.IGNORECASE)
            if value:
                return re.sub(r"\s+", "", value).upper()
        return None

    def _extract_passenger(self, text: str) -> str | None:
        patterns = [
            r"(?:Пассажир|Passenger|Жолаушы)\s*[:\-/\s]*([А-ЯЁA-Z][а-яёa-z]+\s*[А-ЯЁA-Z][а-яёa-z]+)",
            r"(?:Ф\.И\.О\.?|ФИО)\s*[:\-/\s]*([А-ЯЁA-Z][а-яёa-z]+\s+[А-ЯЁA-Z][а-яёa-z]+)",
            r"(?:Покупатель|Заказчик|Buyer)\s*[:\-/\s]*([А-ЯЁA-Z][а-яёa-z]+\s*[А-ЯЁA-Z][а-яёa-z]+)",
        ]
        for pattern in patterns:
            value = self._extract(pattern, text)
            if value:
                return value
        return None

    def _extract_departure(self, text: str) -> str | None:
        value = self._extract_iata_by_city(text, prefer_first=True)
        if value:
            return value

        patterns = [
            r"(?:Аэропорт\s*вылета|Departure\s*airport|Вылет|From)\s*[:\-/\s.]*.*?\(([A-Z]{3})\)",
        ]
        for pattern in patterns:
            value = self._extract(pattern, text)
            if value:
                return value.upper()
        return self._first_airport(text)

    def _extract_arrival(self, text: str) -> str | None:
        value = self._extract_iata_by_city(text, prefer_first=False)
        if value:
            return value

        patterns = [
            r"(?:Аэропорт\s*прилета|Arrival\s*airport|Прилет|To)\s*[:\-/\s.]*.*?\(([A-Z]{3})\)",
        ]
        for pattern in patterns:
            value = self._extract(pattern, text)
            if value:
                return value.upper()
        return self._second_airport(text)

    def _extract_iata_by_city(self, text: str, prefer_first: bool) -> str | None:
        lower_text = text.lower()
        found = []
        for city, iata in CITY_TO_IATA.items():
            if city.lower() in lower_text:
                found.append(iata)
        if not found:
            return None
        if len(found) == 1:
            return found[0]
        return found[0] if prefer_first else found[-1]

    def _extract_seat(self, text: str) -> str | None:
        match = re.search(r"(?:Seat|Место)\s*[:\-/\s]*([0-9]{1,3}[A-F])", text, re.IGNORECASE)
        return match.group(1).strip().upper() if match else None

    def _first_airport(self, text: str) -> str | None:
        codes = re.findall(r"\(([A-Z]{3})\)", text)
        return codes[0].upper() if codes else None

    def _second_airport(self, text: str) -> str | None:
        codes = re.findall(r"\(([A-Z]{3})\)", text)
        return codes[1].upper() if len(codes) > 1 else None
