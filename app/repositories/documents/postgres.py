import json
from sqlalchemy import asc, delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Document
from app.repositories.documents.base import DocumentCreate, DocumentRecord, DocumentRepository


class PostgresDocumentRepository(DocumentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_document(self, payload: DocumentCreate) -> DocumentRecord:
        model = Document(
            title=payload.title,
            content=payload.content,
            metadata_json=json.dumps(payload.metadata) if payload.metadata is not None else None,
            embedding=json.dumps(payload.embedding) if payload.embedding is not None else None,
        )
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_document_record(model)

    async def get_document(self, *, document_id: str) -> DocumentRecord | None:
        stmt = select(Document).where(Document.id == document_id)
        row = await self.session.scalar(stmt)
        if row is None:
            return None
        return self._to_document_record(row)

    async def list_documents(self, *, limit: int = 100) -> list[DocumentRecord]:
        stmt = select(Document).order_by(desc(Document.created_at)).limit(limit)
        rows = (await self.session.execute(stmt)).scalars().all()
        return [self._to_document_record(row) for row in rows]

    async def delete_document(self, *, document_id: str) -> bool:
        stmt = select(Document).where(Document.id == document_id)
        model = await self.session.scalar(stmt)
        if model is None:
            return False
        await self.session.delete(model)
        await self.session.commit()
        return True

    @staticmethod
    def _to_document_record(model: Document) -> DocumentRecord:
        metadata = json.loads(model.metadata_json) if model.metadata_json else None
        embedding = json.loads(model.embedding) if model.embedding else None
        return DocumentRecord(
            id=model.id,
            title=model.title,
            content=model.content,
            metadata=metadata,
            embedding=embedding,
            created_at=model.created_at,
        )
