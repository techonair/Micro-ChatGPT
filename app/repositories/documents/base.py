from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DocumentCreate:
    title: str | None
    content: str
    metadata: dict[str, str] | None = None
    embedding: list[float] | None = None


@dataclass
class DocumentRecord:
    id: str
    title: str | None
    content: str
    metadata: dict[str, str] | None
    embedding: list[float] | None
    created_at: datetime


class DocumentRepository(ABC):
    @abstractmethod
    async def add_document(self, payload: DocumentCreate) -> DocumentRecord:
        raise NotImplementedError

    @abstractmethod
    async def get_document(self, *, document_id: str) -> DocumentRecord | None:
        raise NotImplementedError

    @abstractmethod
    async def list_documents(self, *, limit: int = 100) -> list[DocumentRecord]:
        raise NotImplementedError

    @abstractmethod
    async def delete_document(self, *, document_id: str) -> bool:
        raise NotImplementedError
