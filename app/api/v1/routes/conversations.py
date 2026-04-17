from fastapi import APIRouter, Depends, Query

from app.api.deps import get_conversation_service
from app.schemas.chat import ChatResponse
from app.schemas.common import ApiResponse, ok
from app.schemas.conversation import (
    ConversationCreateRequest,
    ConversationCreateResponse,
    ConversationDeleteResponse,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationMessageRequest,
)
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ApiResponse[ConversationCreateResponse])
async def create_conversation(
    payload: ConversationCreateRequest,
    service: ConversationService = Depends(get_conversation_service),
) -> ApiResponse[ConversationCreateResponse]:
    result = await service.create_conversation(payload)
    return ok(result)


@router.get("", response_model=ApiResponse[ConversationListResponse])
async def list_conversations(
    user_id: str = Query(...),
    service: ConversationService = Depends(get_conversation_service),
) -> ApiResponse[ConversationListResponse]:
    result = await service.list_conversations(user_id=user_id)
    return ok(result)


@router.get("/{conversation_id}", response_model=ApiResponse[ConversationDetailResponse])
async def conversation_detail(
    conversation_id: str,
    user_id: str = Query(...),
    service: ConversationService = Depends(get_conversation_service),
) -> ApiResponse[ConversationDetailResponse]:
    result = await service.get_conversation(user_id=user_id, conversation_id=conversation_id)
    return ok(result)


@router.post("/{conversation_id}/messages", response_model=ApiResponse[ChatResponse])
async def add_message(
    conversation_id: str,
    payload: ConversationMessageRequest,
    service: ConversationService = Depends(get_conversation_service),
) -> ApiResponse[ChatResponse]:
    result = await service.add_message(conversation_id=conversation_id, payload=payload)
    return ok(result)


@router.delete("/{conversation_id}", response_model=ApiResponse[ConversationDeleteResponse])
async def delete_conversation(
    conversation_id: str,
    user_id: str = Query(...),
    service: ConversationService = Depends(get_conversation_service),
) -> ApiResponse[ConversationDeleteResponse]:
    result = await service.delete_conversation(user_id=user_id, conversation_id=conversation_id)
    return ok(result)
