from abc import ABC, abstractmethod


class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_bytes: bytes, filename: str) -> dict:
        """Parse document bytes and return structured dict."""
        ...

    @abstractmethod
    def doc_type(self) -> str:
        ...
