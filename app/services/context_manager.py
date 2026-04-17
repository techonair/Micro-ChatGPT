from collections.abc import Sequence

from app.repositories.conversations.base import (
    ConversationRepository,
    ConversationSummaryCreate,
    ConversationTurnRecord,
)
from app.services.llm.base import ChatMessage
from app.services.rag_service import RAGService


class ContextManager:
    def __init__(self, *, settings, repo: ConversationRepository, rag_service: RAGService) -> None:
        self.settings = settings
        self.repo = repo
        self.rag_service = rag_service

    async def build_messages(
        self,
        *,
        user_id: str,
        session_id: str,
        provider: str,
        user_message: str,
        use_rag: bool = False,
        top_k: int = 3,
    ) -> list[ChatMessage]:
        messages: list[ChatMessage] = []
        if use_rag:
            messages.extend(await self._build_rag_context(user_message=user_message, top_k=top_k))

        messages.extend(await self._build_from_repository(user_id=user_id, session_id=session_id))
        messages.append(ChatMessage(role="user", content=user_message))
        messages = await self._fit_context_limit(
            messages=messages,
            user_id=user_id,
            session_id=session_id,
            provider=provider,
        )
        return messages

    async def _build_rag_context(self, *, user_message: str, top_k: int) -> list[ChatMessage]:
        snippets = await self.rag_service.search(query=user_message, top_k=top_k)
        if not snippets:
            return []

        document_payload = "\n\n".join(
            self._format_document(index + 1, snippet)
            for index, snippet in enumerate(snippets)
        )
        instructions = (
            "You are a helpful assistant. Use only the following documents to answer the user’s question. "
            "If the answer is not contained in these documents, say you do not know. Do not hallucinate.\n\n"
            f"{document_payload}"
        )

        return [ChatMessage(role="system", content=instructions)]

    @staticmethod
    def _format_document(index: int, snippet) -> str:
        title = snippet.title or "Untitled document"
        content = snippet.content.strip()
        if len(content) > 1200:
            content = content[:1200].rsplit(" ", 1)[0] + "..."
        return f"Document {index}: {title}\n{content}"

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
