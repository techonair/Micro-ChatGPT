from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ConversationTurnCreate:
    user_id: str
    session_id: str
    provider: str
    model: str
    input_text: str
    output_text: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float


@dataclass
class ConversationTurnRecord:
    id: str
    user_id: str
    session_id: str
    timestamp: datetime
    provider: str
    model: str
    input_text: str
    output_text: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float


@dataclass
class ConversationSummaryCreate:
    user_id: str
    session_id: str
    summary_text: str
    covered_until: datetime


@dataclass
class ConversationSummaryRecord:
    id: str
    user_id: str
    session_id: str
    summary_text: str
    covered_until: datetime
    created_at: datetime


@dataclass
class ConversationSessionRecord:
    session_id: str
    started_at: datetime
    updated_at: datetime
    turn_count: int


class ConversationRepository(ABC):
    @abstractmethod
    async def add_turn(self, payload: ConversationTurnCreate) -> ConversationTurnRecord:
        raise NotImplementedError

    @abstractmethod
    async def list_turns(
        self,
        *,
        user_id: str,
        session_id: str | None = None,
        limit: int = 100,
    ) -> list[ConversationTurnRecord]:
        raise NotImplementedError

    @abstractmethod
    async def recent_turns(self, *, user_id: str, session_id: str, limit: int = 20) -> list[ConversationTurnRecord]:
        raise NotImplementedError

    @abstractmethod
    async def add_summary(self, payload: ConversationSummaryCreate) -> ConversationSummaryRecord:
        raise NotImplementedError

    @abstractmethod
    async def list_summaries(
        self,
        *,
        user_id: str,
        session_id: str | None = None,
        limit: int = 20,
    ) -> list[ConversationSummaryRecord]:
        raise NotImplementedError

    @abstractmethod
    async def list_sessions(self, *, user_id: str, limit: int = 100) -> list[ConversationSessionRecord]:
        raise NotImplementedError

    @abstractmethod
    async def session_exists(self, *, user_id: str, session_id: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def conversation_turns(
        self,
        *,
        user_id: str,
        session_id: str,
        limit: int = 500,
    ) -> list[ConversationTurnRecord]:
        raise NotImplementedError

    @abstractmethod
    async def delete_session(self, *, user_id: str, session_id: str) -> bool:
        raise NotImplementedError
