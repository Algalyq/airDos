import re

from app.services.parsers.base import BaseParser
from app.services.parsers.ocr import extract_text_from_bytes

CITY_TO_IATA = {
    "астана": "NQZ",
    "ата": "NQZ",
    "алматы": "ALA",
    "шымкент": "CIT",
    "актобе": "AKX",
    "атырау": "GUW",
    "орал": "URA",
    "павлодар": "PWQ",
    "караганда": "KGF",
    "тараз": "DMB",
    "костанай": "KSN",
    "nursultan": "NQZ",
    "nur-sultan": "NQZ",
}


class BoardingPassParser(BaseParser):
    def doc_type(self) -> str:
        return "boarding_pass"

    def parse(self, file_bytes: bytes, filename: str, content_type: str | None = None) -> dict:
        text = extract_text_from_bytes(file_bytes, content_type, filename)
        return {
            "document_type": "boarding_pass",
            "airline": self._extract_airline(text),
            "flight_number": self._extract_flight(text),
            "passenger_name": self._extract_passenger(text),
            "identity_document": self._extract_identity_document(text),
            "ticket_number": self._extract_ticket_number(text),
            "booking_reference": self._extract_booking_reference(text),
            "departure": self._extract_departure(text),
            "departure_time": self._extract_departure_time(text),
            "arrival": self._extract_arrival(text),
            "arrival_time": self._extract_arrival_time(text),
            "flight_date": self._extract_flight_date(text),
            "class": self._extract_class(text),
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

    def _extract_airline(self, text: str) -> str | None:
        upper = text.upper()
        if "SCAT" in upper or "СКАТ" in upper:
            return "SCAT"
        if "FLYARYSTAN" in upper or "ЭЙР АСТАНА" in upper or "AIR ASTANA" in upper:
            return "FlyArystan"
        if "QAZAQ AIR" in upper or "QAZAQAIR" in upper:
            return "Qazaq Air"
        if "BEEBARJET" in upper or "BEE BARJET" in upper:
            return "BeeBarjet"

        match = re.search(r"(?:Авиакомпания|Airline|airline)\s*[:\-/\s.]+([A-Za-z]{2,})", text, re.IGNORECASE)
        if match:
            value = match.group(1).strip().upper()
            if value != "AIRLINE":
                return value

        flight = self._extract_flight(text)
        if flight:
            prefix = flight[:2]
            prefix_to_airline = {
                "DV": "SCAT",
                "KC": "Air Astana",
                "FS": "FlyArystan",
            }
            if prefix in prefix_to_airline:
                return prefix_to_airline[prefix]
        return None

    def _extract_flight(self, text: str) -> str | None:
        patterns = [
            r"(?:Рейс|рейс|Номер\s*рейса|Flight\s*number|Flight)\s*[:\-/\s.]*([A-Z]{2,3}[\s\-]?\d{2,4})",
            r"(?:SCAT|СКАТ|airline|авиакомпания).*?\b([A-Z]{2}[\s\-]?\d{3,4})\b",
            r"\b([A-Z]{2}[\s\-]?\d{3,4})\b",
        ]
        for pattern in patterns:
            value = self._extract(pattern, text, flags=re.IGNORECASE)
            if value:
                return re.sub(r"[\s\-]+", "", value).upper()
        return None

    def _extract_identity_document(self, text: str) -> str | None:
        match = re.search(
            r"(?:Документ\s*удостоверя[ющийш]+\s*личность|Identity\s*document)\s*[:\-/\s]*([0-9]+)",
            text,
            re.IGNORECASE,
        )
        if match:
            return match.group(1).strip()
        match = re.search(
            r"[A-Z]{2,}(?:\s+[A-Z]{2,})+\s+(?:Взрослый|Детский|Младенец|Adult|Child|Infant)\s+.*?\b(\d{9})\b",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        return match.group(1).strip() if match else None

    def _extract_ticket_number(self, text: str) -> str | None:
        match = re.search(r"(?:Номер\s*билета|Ticket\s*number)\s*[:\-/\s]*([0-9]{3}[\-]?[0-9]{10})", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        match = re.search(r"\b(\d{3}-\d{10})\b", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        match = re.search(r"(?:номер\s*билета|ticket\s*number).*?\b(\d{13})\b", text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        match = re.search(r"[A-Z]{6}\s+(\d{13})", text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _extract_booking_reference(self, text: str) -> str | None:
        patterns = [
            r"(?:Aviata\.kz|avia\.kz|bilet\.kz)\s+([A-Z]{6})",
            r"(?:[HН][oо][МM][eе][pр]\s*брони|брони|Номер\s*брони|Booking\s*Reference|PNR|Order)\s*[:\-/\s]*([A-Z]{6})",
            r"([A-Z]{6})\s+\d{13}\s*\n\s*номер\s*брони",
            r"([A-Z]{6})\s+\d{13}",
            r"(?:Номер\s*заказа|Order)\s*[:\-/\s]*([A-Z]{6})(?![A-Z])",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip().upper()
                if value == "FREEDO":
                    continue
                return value
        return None

    def _extract_departure_time(self, text: str) -> str | None:
        codes = re.findall(r"\b([0-9]{2}:[0-9]{2})\b", text)
        return codes[0] if codes else None

    def _extract_arrival_time(self, text: str) -> str | None:
        codes = re.findall(r"\b([0-9]{2}:[0-9]{2})\b", text)
        return codes[1] if len(codes) > 1 else None

    def _extract_flight_date(self, text: str) -> str | None:
        non_flight_keywords = [
            "рождения", "birth", "дата рождения", "свидетельство", "ндс", "регистрация",
            "бин", "выдан", "issued", "постановке", "учёт", "tax", "vat", "серия", "выписки",
        ]

        flight_date_patterns = [
            r"(?:Рейс|Flight|рейс|Вылет|Departure|Прилет|Arrival|Дата\s*вылета|Дата).*?(\d{1,2}\.[0-9]{2}\.\d{4})",
            r"(?:Рейс|Flight|рейс|Вылет|Departure|Прилет|Arrival|Дата\s*вылета|Дата).*?(\d{1,2}\s+[а-яё]+\s+\d{4})",
        ]
        for pattern in flight_date_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE | re.DOTALL))
            for m in matches:
                pos = m.start(1)
                nearby = text[max(0, pos - 100):pos + 50].lower()
                if any(word in nearby for word in non_flight_keywords):
                    continue
                return m.group(1).strip()

        for pattern in [r"(\d{1,2}\.[0-9]{2}\.\d{4})", r"(\d{1,2}\s+[а-яё]+\s+\d{4})"]:
            for m in re.finditer(pattern, text, re.IGNORECASE):
                pos = m.start()
                nearby = text[max(0, pos - 100):pos + 50].lower()
                if any(word in nearby for word in non_flight_keywords):
                    continue
                return m.group(1).strip()

        return None

    def _extract_class(self, text: str) -> str | None:
        lower = text.lower()
        for word in ("эконом", "economy", "бизнес", "business", "первый", "first", "low"):
            if word in lower:
                mapping = {
                    "эконом": "Эконом",
                    "economy": "Эконом",
                    "бизнес": "Бизнес",
                    "business": "Бизнес",
                    "первый": "Первый",
                    "first": "Первый",
                    "low": "Эконом",
                }
                return mapping[word]
        return None

    def _extract_passenger(self, text: str) -> str | None:
        patterns = [
            r"(?:ФИО\s*пассажира|Ф\.И\.О\.?|Фамилия\s*Имя|Пассажир|Passenger|Жолаушы)\s*[:\-/\s]*([A-Z]{2,}(?:[\s/][A-Z]{2,})+(?:\s+[A-Z])?(?:\s+\d{2}\.\d{2}\.\d{4})?)",
            r"([A-Z]{2,}/[A-Z]{2,})\s*",
            r"([A-Z]{2,}(?:\s+[A-Z]{2,})+)\s+(?:Взрослый|Детский|Младенец|Adult|Child|Infant)",
            r"(?:Покупатель|Заказчик|Buyer)\s*[:\-/\s]*([А-ЯЁA-Z][а-яёa-z]+\s*[А-ЯЁA-Z][а-яёa-z]+)",
            r"\b([A-Z]{2,}(?:\s+[A-Z]{2,})+)\s+\d{9,12}\b",
        ]
        for pattern in patterns:
            value = self._extract(pattern, text)
            if value:
                value = re.sub(r"\s+\d{2}\.\d{2}\.\d{4}$", "", value.strip())
                value = re.sub(r"\s+[A-Z]$", "", value.strip())
                return value.upper().strip()
        return None

    def _extract_departure(self, text: str) -> str | None:
        route = self._extract_route(text)
        if route:
            return route[0]

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
        route = self._extract_route(text)
        if route:
            return route[1]

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

    def _extract_route(self, text: str) -> tuple[str, str] | None:
        match = re.search(r"([А-ЯЁA-Z][а-яёa-z]{2,})\s*[-—>]\s*([А-ЯЁA-Z][а-яёa-z]{2,})", text, re.IGNORECASE)
        if not match:
            return None

        from_city = self._city_to_iata(match.group(1))
        to_city = self._city_to_iata(match.group(2))
        if from_city and to_city:
            return from_city, to_city
        return None

    def _city_to_iata(self, city: str) -> str | None:
        key = city.lower().strip()
        for city_name, iata in CITY_TO_IATA.items():
            if city_name in key or key in city_name:
                return iata
        return None

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
        if match:
            return match.group(1).strip().upper()

        normalized = self._normalize_ocr_latin(text)
        match = re.search(r"(?:\d{1,2}\.\d{2}\.\d{4})\s+(?:[A-Z]{1,4}\s+)?([0-9]{1,3}[A-F])\b", normalized, re.IGNORECASE)
        if match:
            return match.group(1).strip().upper()

        return None

    @staticmethod
    def _normalize_ocr_latin(text: str) -> str:
        mapping = {
            "с": "c", "С": "C",
            "а": "a", "А": "A",
            "е": "e", "Е": "E",
            "о": "o", "О": "O",
            "р": "p", "Р": "P",
            "х": "x", "Х": "X",
        }
        return "".join(mapping.get(ch, ch) for ch in text)

    def _first_airport(self, text: str) -> str | None:
        codes = re.findall(r"\(([A-Z]{3})\)", text)
        return codes[0].upper() if codes else None

    def _second_airport(self, text: str) -> str | None:
        codes = re.findall(r"\(([A-Z]{3})\)", text)
        return codes[1].upper() if len(codes) > 1 else None
