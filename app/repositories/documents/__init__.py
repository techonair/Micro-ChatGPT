from app.repositories.documents.base import DocumentCreate, DocumentRecord, DocumentRepository
from app.repositories.documents.postgres import PostgresDocumentRepository

__all__ = [
    "DocumentCreate",
    "DocumentRecord",
    "DocumentRepository",
    "PostgresDocumentRepository",
]
