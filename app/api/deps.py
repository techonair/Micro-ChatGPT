from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.repositories.conversations.base import ConversationRepository
from app.repositories.conversations.postgres import PostgresConversationRepository
from app.services.auth_service import AuthService
from app.services.chat_service import ChatService
from app.services.conversation_service import ConversationService
from app.services.context_manager import ContextManager
from app.services.cost_tracker import CostTracker
from app.services.history_service import HistoryService
from app.services.llm.factory import LLMProviderFactory


async def get_db(session: AsyncSession = Depends(get_db_session)) -> AsyncSession:
    return session


def get_app_settings() -> Settings:
    return get_settings()


def get_llm_factory() -> LLMProviderFactory:
    return LLMProviderFactory(get_settings())


async def get_conversation_repo(
    db: AsyncSession = Depends(get_db),
) -> ConversationRepository:
    return PostgresConversationRepository(db)


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)


async def get_chat_service(
    db: AsyncSession = Depends(get_db),
    repo: ConversationRepository = Depends(get_conversation_repo),
    settings: Settings = Depends(get_app_settings),
) -> ChatService:
    context_manager = ContextManager(settings=settings, repo=repo)
    return ChatService(
        db_session=db,
        repo=repo,
        llm_factory=get_llm_factory(),
        context_manager=context_manager,
        cost_tracker=CostTracker(),
    )


async def get_history_service(
    repo: ConversationRepository = Depends(get_conversation_repo),
) -> HistoryService:
    return HistoryService(repo)


async def get_conversation_service(
    repo: ConversationRepository = Depends(get_conversation_repo),
    chat_service: ChatService = Depends(get_chat_service),
) -> ConversationService:
    return ConversationService(repo=repo, chat_service=chat_service)
