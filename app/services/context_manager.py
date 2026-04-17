from collections.abc import Sequence

from app.repositories.conversations.base import (
    ConversationRepository,
    ConversationSummaryCreate,
    ConversationTurnRecord,
)
from app.services.llm.base import ChatMessage


class ContextManager:
    def __init__(self, *, settings, repo: ConversationRepository) -> None:
        self.settings = settings
        self.repo = repo

    async def build_messages(
        self,
        *,
        user_id: str,
        session_id: str,
        provider: str,
        user_message: str,
    ) -> list[ChatMessage]:
        messages = await self._build_from_repository(user_id=user_id, session_id=session_id)

        messages.append(ChatMessage(role="user", content=user_message))
        messages = await self._fit_context_limit(
            messages=messages,
            user_id=user_id,
            session_id=session_id,
            provider=provider,
        )
        return messages

    async def _build_from_repository(self, *, user_id: str, session_id: str) -> list[ChatMessage]:
        summaries = await self.repo.list_summaries(user_id=user_id, session_id=session_id, limit=1)
        turns = await self.repo.recent_turns(user_id=user_id, session_id=session_id, limit=25)

        messages: list[ChatMessage] = []
        if summaries:
            messages.append(
                ChatMessage(
                    role="system",
                    content=f"Conversation summary: {summaries[0].summary_text}",
                )
            )

        for turn in turns:
            messages.append(ChatMessage(role="user", content=turn.input_text))
            messages.append(ChatMessage(role="assistant", content=turn.output_text))
        return messages

    async def _fit_context_limit(
        self,
        *,
        messages: list[ChatMessage],
        user_id: str,
        session_id: str,
        provider: str,
    ) -> list[ChatMessage]:
        limit = self.settings.provider_context_limits.get(provider, 8000)
        if self._approx_tokens(messages) <= limit:
            return messages

        turns = await self.repo.recent_turns(user_id=user_id, session_id=session_id, limit=25)
        if len(turns) >= 6:
            midpoint = len(turns) // 2
            to_summarize = turns[:midpoint]
            summary_text = self._summarize_turns(to_summarize)
            await self.repo.add_summary(
                ConversationSummaryCreate(
                    user_id=user_id,
                    session_id=session_id,
                    summary_text=summary_text,
                    covered_until=to_summarize[-1].timestamp,
                )
            )
            retained = turns[midpoint:]
            compact = [ChatMessage(role="system", content=f"Conversation summary: {summary_text}")]
            for turn in retained:
                compact.append(ChatMessage(role="user", content=turn.input_text))
                compact.append(ChatMessage(role="assistant", content=turn.output_text))
            # Keep the latest user message if trimming removed it.
            if messages and messages[-1].role == "user":
                compact.append(messages[-1])
            messages = compact

        while self._approx_tokens(messages) > limit and len(messages) > 3:
            messages.pop(0)

        return messages

    @staticmethod
    def _summarize_turns(turns: Sequence[ConversationTurnRecord]) -> str:
        snippets = []
        for turn in turns[-8:]:
            user_part = turn.input_text.strip().replace("\n", " ")[:120]
            assistant_part = turn.output_text.strip().replace("\n", " ")[:120]
            snippets.append(f"U: {user_part} | A: {assistant_part}")
        return " ; ".join(snippets)

    @staticmethod
    def _approx_tokens(messages: list[ChatMessage]) -> int:
        return sum(max(1, len(m.content) // 4) for m in messages)
