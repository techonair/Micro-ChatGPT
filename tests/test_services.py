from datetime import UTC, datetime

import pytest

from app.repositories.conversations.base import (
    ConversationRepository,
    ConversationSessionRecord,
    ConversationSummaryCreate,
    ConversationSummaryRecord,
    ConversationTurnCreate,
    ConversationTurnRecord,
)
from app.services.context_manager import ContextManager
from app.services.cost_tracker import CostTracker


class FakeRepo(ConversationRepository):
    def __init__(self):
        self.turns: list[ConversationTurnRecord] = []
        self.summaries: list[ConversationSummaryRecord] = []

    async def add_turn(self, payload: ConversationTurnCreate) -> ConversationTurnRecord:
        row = ConversationTurnRecord(
            id=f"turn-{len(self.turns)+1}",
            timestamp=datetime.now(UTC),
            **payload.__dict__,
        )
        self.turns.append(row)
        return row

    async def list_turns(self, *, user_id: str, session_id: str | None = None, limit: int = 100):
        rows = [t for t in self.turns if t.user_id == user_id and (session_id is None or t.session_id == session_id)]
        return list(reversed(rows[-limit:]))

    async def recent_turns(self, *, user_id: str, session_id: str, limit: int = 20):
        rows = [t for t in self.turns if t.user_id == user_id and t.session_id == session_id]
        return rows[-limit:]

    async def add_summary(self, payload: ConversationSummaryCreate):
        row = ConversationSummaryRecord(
            id=f"summary-{len(self.summaries)+1}",
            created_at=datetime.now(UTC),
            **payload.__dict__,
        )
        self.summaries.append(row)
        return row

    async def list_summaries(self, *, user_id: str, session_id: str | None = None, limit: int = 20):
        rows = [s for s in self.summaries if s.user_id == user_id and (session_id is None or s.session_id == session_id)]
        return list(reversed(rows[-limit:]))

    async def list_sessions(self, *, user_id: str, limit: int = 100):
        sessions: dict[str, list[ConversationTurnRecord]] = {}
        for turn in self.turns:
            if turn.user_id != user_id:
                continue
            sessions.setdefault(turn.session_id, []).append(turn)

        records: list[ConversationSessionRecord] = []
        for session_id, turns in sessions.items():
            ordered = sorted(turns, key=lambda t: t.timestamp)
            records.append(
                ConversationSessionRecord(
                    session_id=session_id,
                    started_at=ordered[0].timestamp,
                    updated_at=ordered[-1].timestamp,
                    turn_count=len(ordered),
                )
            )
        records.sort(key=lambda r: r.updated_at, reverse=True)
        return records[:limit]

    async def session_exists(self, *, user_id: str, session_id: str) -> bool:
        return any(t.user_id == user_id and t.session_id == session_id for t in self.turns)

    async def conversation_turns(self, *, user_id: str, session_id: str, limit: int = 500):
        rows = [t for t in self.turns if t.user_id == user_id and t.session_id == session_id]
        rows.sort(key=lambda t: t.timestamp)
        return rows[:limit]

    async def delete_session(self, *, user_id: str, session_id: str) -> bool:
        before_turns = len(self.turns)
        self.turns = [t for t in self.turns if not (t.user_id == user_id and t.session_id == session_id)]
        self.summaries = [s for s in self.summaries if not (s.user_id == user_id and s.session_id == session_id)]
        return len(self.turns) != before_turns


class TinySettings:
    provider_context_limits = {"openai": 30}


@pytest.mark.asyncio
async def test_context_manager_creates_summary_when_context_exceeds_limit():
    repo = FakeRepo()
    for i in range(8):
        await repo.add_turn(
            ConversationTurnCreate(
                user_id="u1",
                session_id="s1",
                provider="openai",
                model="gpt-4o-mini",
                input_text=f"input {i} " * 20,
                output_text=f"output {i} " * 20,
                prompt_tokens=10,
                completion_tokens=10,
                total_tokens=20,
                estimated_cost=0.001,
            )
        )

    cm = ContextManager(settings=TinySettings(), repo=repo)
    messages = await cm.build_messages(user_id="u1", session_id="s1", provider="openai", user_message="new msg")

    assert len(messages) > 0
    assert len(repo.summaries) >= 1


def test_cost_tracker_estimation():
    tracker = CostTracker()
    cost = tracker.estimate(provider="openai", prompt_tokens=1000, completion_tokens=1000)
    assert cost > 0
