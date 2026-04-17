from fastapi import APIRouter, Depends

from app.api.deps import get_rag_service
from app.schemas.common import ApiResponse, ok
from app.schemas.document import DocumentCreateRequest, DocumentResponse
from app.repositories.documents.base import DocumentCreate
from app.services.rag_service import RAGService

router = APIRouter(tags=["documents"])


@router.post("/documents", response_model=ApiResponse[DocumentResponse])
async def create_document(
    payload: DocumentCreateRequest,
    service: RAGService = Depends(get_rag_service),
) -> ApiResponse[DocumentResponse]:
    document = await service.add_document(
        payload=DocumentCreate(
            title=payload.title,
            content=payload.content,
            metadata=payload.metadata,
        )
    )
    return ok(DocumentResponse(
        id=document.id,
        title=document.title,
        content=document.content,
        metadata=document.metadata,
        created_at=document.created_at,
    ))


@router.get("/documents", response_model=ApiResponse[list[DocumentResponse]])
async def list_documents(
    service: RAGService = Depends(get_rag_service),
) -> ApiResponse[list[DocumentResponse]]:
    documents = await service.repo.list_documents(limit=100)
    response_data = [
        DocumentResponse(
            id=document.id,
            title=document.title,
            content=document.content,
            metadata=document.metadata,
            created_at=document.created_at,
        )
        for document in documents
    ]
    return ok(response_data)
