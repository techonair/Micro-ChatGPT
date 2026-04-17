import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.errors import AppError
from app.db.models import User
from app.repositories.conversations.base import ConversationRepository, ConversationTurnCreate
from app.schemas.chat import ChatRequest, ChatResponse, TokenUsage
from app.services.context_manager import ContextManager
from app.services.cost_tracker import CostTracker
from app.services.llm.factory import LLMProviderFactory
from app.services.rag_service import RAGService
from app.utils.monitoring import LLM_CALL_COUNT


class ChatService:
    def __init__(
        self,
        *,
        db_session: AsyncSession,
        repo: ConversationRepository,
        llm_factory: LLMProviderFactory,
        context_manager: ContextManager,
        cost_tracker: CostTracker,
        rag_service: RAGService,
    ) -> None:
        self.db_session = db_session
        self.repo = repo
        self.llm_factory = llm_factory
        self.context_manager = context_manager
        self.cost_tracker = cost_tracker
        self.rag_service = rag_service

    async def send_message(self, payload: ChatRequest) -> ChatResponse:
        user_exists = await self.db_session.scalar(select(User.id).where(User.id == payload.user_id))
        if not user_exists:
            raise AppError("User not found", status_code=404, code="user_not_found")

        session_id = payload.session_id or str(uuid.uuid4())
        provider_name = payload.provider.value
        provider = self.llm_factory.get(provider_name)

        messages = await self.context_manager.build_messages(
            user_id=payload.user_id,
            session_id=session_id,
            provider=provider_name,
            user_message=payload.message,
            use_rag=payload.use_rag,
            top_k=payload.top_k,
        )

        model = payload.model or ""
        try:
            result = await self._generate_with_retry(provider, model=model, messages=messages)
            LLM_CALL_COUNT.labels(provider=provider_name, model=result.model, status="success").inc()
        except Exception as exc:
            LLM_CALL_COUNT.labels(provider=provider_name, model=model or "unknown", status="failure").inc()
            raise AppError("LLM provider call failed", status_code=502, code="llm_failure") from exc

        estimated_cost = self.cost_tracker.estimate(
            provider=provider_name,
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
        )

        turn = await self.repo.add_turn(
            ConversationTurnCreate(
                user_id=payload.user_id,
                session_id=session_id,
                provider=provider_name,
                model=result.model,
                input_text=payload.message,
                output_text=result.output_text,
                prompt_tokens=result.prompt_tokens,
                completion_tokens=result.completion_tokens,
                total_tokens=result.total_tokens,
                estimated_cost=estimated_cost,
            )
        )

        return ChatResponse(
            session_id=session_id,
            provider=payload.provider,
            model=result.model,
            output_text=result.output_text,
            token_usage=TokenUsage(
                prompt_tokens=turn.prompt_tokens,
                completion_tokens=turn.completion_tokens,
                total_tokens=turn.total_tokens,
                estimated_cost=turn.estimated_cost,
            ),
            timestamp=turn.timestamp,
        )

    async def _generate_with_retry(self, provider, *, model: str, messages):
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(min=1, max=8),
            retry=retry_if_exception_type(Exception),
            reraise=True,
        ):
            with attempt:
                return await provider.generate(model=model, messages=messages)
