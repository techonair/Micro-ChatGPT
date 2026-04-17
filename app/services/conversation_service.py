from app.core.errors import AppError
from app.repositories.conversations.base import ConversationRepository
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.conversation import (
    ConversationCreateRequest,
    ConversationCreateResponse,
    ConversationDeleteResponse,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationMessageRequest,
    ConversationSessionOut,
)
from app.schemas.history import ConversationSummaryOut, ConversationTurnOut
from app.services.chat_service import ChatService


class ConversationService:
    def __init__(self, *, repo: ConversationRepository, chat_service: ChatService) -> None:
        self.repo = repo
        self.chat_service = chat_service

    async def create_conversation(self, payload: ConversationCreateRequest) -> ConversationCreateResponse:
        first = await self.chat_service.send_message(
            ChatRequest(
                user_id=payload.user_id,
                message=payload.message,
                provider=payload.provider,
                model=payload.model,
            )
        )
        return ConversationCreateResponse(conversation_id=first.session_id, first_message=first)

    async def list_conversations(self, *, user_id: str) -> ConversationListResponse:
        sessions = await self.repo.list_sessions(user_id=user_id, limit=200)
        return ConversationListResponse(
            conversations=[
                ConversationSessionOut(
                    conversation_id=s.session_id,
                    started_at=s.started_at,
                    updated_at=s.updated_at,
                    turn_count=s.turn_count,
                )
                for s in sessions
            ]
        )

    async def get_conversation(self, *, user_id: str, conversation_id: str) -> ConversationDetailResponse:
        exists = await self.repo.session_exists(user_id=user_id, session_id=conversation_id)
        if not exists:
            raise AppError("Conversation not found", status_code=404, code="conversation_not_found")

        turns = await self.repo.conversation_turns(user_id=user_id, session_id=conversation_id, limit=1000)
        summaries = await self.repo.list_summaries(user_id=user_id, session_id=conversation_id, limit=100)

        return ConversationDetailResponse(
            conversation_id=conversation_id,
            turns=[ConversationTurnOut(**t.__dict__) for t in turns],
            summaries=[ConversationSummaryOut(**s.__dict__) for s in summaries],
        )

    async def add_message(
        self,
        *,
        conversation_id: str,
        payload: ConversationMessageRequest,
    ) -> ChatResponse:
        exists = await self.repo.session_exists(user_id=payload.user_id, session_id=conversation_id)
        if not exists:
            raise AppError("Conversation not found", status_code=404, code="conversation_not_found")

        return await self.chat_service.send_message(
            ChatRequest(
                user_id=payload.user_id,
                message=payload.message,
                session_id=conversation_id,
                provider=payload.provider,
                model=payload.model,
            )
        )

    async def delete_conversation(self, *, user_id: str, conversation_id: str) -> ConversationDeleteResponse:
        deleted = await self.repo.delete_session(user_id=user_id, session_id=conversation_id)
        if not deleted:
            raise AppError("Conversation not found", status_code=404, code="conversation_not_found")

        return ConversationDeleteResponse(conversation_id=conversation_id, deleted=True)
