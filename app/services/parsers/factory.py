from app.services.parsers.base import BaseParser
from app.services.parsers.boarding import BoardingPassParser
from app.services.parsers.id_card import KzIdParser
from app.services.parsers.passport import PassportParser


PARSERS: dict[str, type[BaseParser]] = {
    BoardingPassParser().doc_type(): BoardingPassParser,
    KzIdParser().doc_type(): KzIdParser,
    PassportParser().doc_type(): PassportParser,
}


def get_parser(doc_type: str) -> BaseParser:
    parser_cls = PARSERS.get(doc_type)
    if parser_cls is None:
        supported = ", ".join(PARSERS.keys())
        raise ValueError(f"Unsupported doc_type '{doc_type}'. Supported: {supported}")
    return parser_cls()


def parse_document(doc_type: str, file_bytes: bytes, filename: str, content_type: str | None = None) -> dict:
    parser = get_parser(doc_type)
    return parser.parse(file_bytes, filename, content_type)
