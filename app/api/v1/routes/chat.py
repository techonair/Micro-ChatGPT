from fastapi import APIRouter, Depends

from app.api.deps import get_chat_service
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.common import ApiResponse, ok
from app.services.chat_service import ChatService

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ApiResponse[ChatResponse])
async def chat(
    payload: ChatRequest,
    service: ChatService = Depends(get_chat_service),
) -> ApiResponse[ChatResponse]:
    result = await service.send_message(payload)
    return ok(result)
