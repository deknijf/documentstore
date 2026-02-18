from abc import ABC, abstractmethod


class OCRProvider(ABC):
    @abstractmethod
    def extract_text(self, file_path: str, content_type: str) -> str:
        raise NotImplementedError
