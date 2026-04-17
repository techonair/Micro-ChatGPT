from sqlalchemy import asc, delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ConversationSummary, ConversationTurn
from app.repositories.conversations.base import (
    ConversationRepository,
    ConversationSessionRecord,
    ConversationSummaryCreate,
    ConversationSummaryRecord,
    ConversationTurnCreate,
    ConversationTurnRecord,
)


class PostgresConversationRepository(ConversationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_turn(self, payload: ConversationTurnCreate) -> ConversationTurnRecord:
        model = ConversationTurn(**payload.__dict__)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_turn_record(model)

    async def list_turns(
        self,
        *,
        user_id: str,
        session_id: str | None = None,
        limit: int = 100,
    ) -> list[ConversationTurnRecord]:
        stmt = select(ConversationTurn).where(ConversationTurn.user_id == user_id)
        if session_id:
            stmt = stmt.where(ConversationTurn.session_id == session_id)
        stmt = stmt.order_by(desc(ConversationTurn.timestamp)).limit(limit)
        rows = (await self.session.execute(stmt)).scalars().all()
        return [self._to_turn_record(r) for r in rows]

    async def recent_turns(self, *, user_id: str, session_id: str, limit: int = 20) -> list[ConversationTurnRecord]:
        stmt = (
            select(ConversationTurn)
            .where(ConversationTurn.user_id == user_id, ConversationTurn.session_id == session_id)
            .order_by(desc(ConversationTurn.timestamp))
            .limit(limit)
        )
        rows = (await self.session.execute(stmt)).scalars().all()
        records = [self._to_turn_record(r) for r in rows]
        return list(reversed(records))

    async def add_summary(self, payload: ConversationSummaryCreate) -> ConversationSummaryRecord:
        model = ConversationSummary(**payload.__dict__)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_summary_record(model)

    async def list_summaries(
        self,
        *,
        user_id: str,
        session_id: str | None = None,
        limit: int = 20,
    ) -> list[ConversationSummaryRecord]:
        stmt = select(ConversationSummary).where(ConversationSummary.user_id == user_id)
        if session_id:
            stmt = stmt.where(ConversationSummary.session_id == session_id)
        stmt = stmt.order_by(desc(ConversationSummary.covered_until)).limit(limit)
        rows = (await self.session.execute(stmt)).scalars().all()
        return [self._to_summary_record(r) for r in rows]

    async def list_sessions(self, *, user_id: str, limit: int = 100) -> list[ConversationSessionRecord]:
        stmt = (
            select(
                ConversationTurn.session_id,
                func.min(ConversationTurn.timestamp).label("started_at"),
                func.max(ConversationTurn.timestamp).label("updated_at"),
                func.count(ConversationTurn.id).label("turn_count"),
            )
            .where(ConversationTurn.user_id == user_id)
            .group_by(ConversationTurn.session_id)
            .order_by(desc(func.max(ConversationTurn.timestamp)))
            .limit(limit)
        )
        rows = (await self.session.execute(stmt)).all()
        return [
            ConversationSessionRecord(
                session_id=row.session_id,
                started_at=row.started_at,
                updated_at=row.updated_at,
                turn_count=int(row.turn_count),
            )
            for row in rows
        ]

    async def session_exists(self, *, user_id: str, session_id: str) -> bool:
        stmt = (
            select(ConversationTurn.id)
            .where(ConversationTurn.user_id == user_id, ConversationTurn.session_id == session_id)
            .limit(1)
        )
        row = await self.session.scalar(stmt)
        return row is not None

    async def conversation_turns(
        self,
        *,
        user_id: str,
        session_id: str,
        limit: int = 500,
    ) -> list[ConversationTurnRecord]:
        stmt = (
            select(ConversationTurn)
            .where(ConversationTurn.user_id == user_id, ConversationTurn.session_id == session_id)
            .order_by(asc(ConversationTurn.timestamp))
            .limit(limit)
        )
        rows = (await self.session.execute(stmt)).scalars().all()
        return [self._to_turn_record(r) for r in rows]

    async def delete_session(self, *, user_id: str, session_id: str) -> bool:
        exists = await self.session_exists(user_id=user_id, session_id=session_id)
        if not exists:
            return False

        await self.session.execute(
            delete(ConversationSummary).where(
                ConversationSummary.user_id == user_id,
                ConversationSummary.session_id == session_id,
            )
        )
        await self.session.execute(
            delete(ConversationTurn).where(
                ConversationTurn.user_id == user_id,
                ConversationTurn.session_id == session_id,
            )
        )
        await self.session.commit()
        return True

    @staticmethod
    def _to_turn_record(model: ConversationTurn) -> ConversationTurnRecord:
        return ConversationTurnRecord(
            id=model.id,
            user_id=model.user_id,
            session_id=model.session_id,
            timestamp=model.timestamp,
            provider=model.provider,
            model=model.model,
            input_text=model.input_text,
            output_text=model.output_text,
            prompt_tokens=model.prompt_tokens,
            completion_tokens=model.completion_tokens,
            total_tokens=model.total_tokens,
            estimated_cost=model.estimated_cost,
        )

    @staticmethod
    def _to_summary_record(model: ConversationSummary) -> ConversationSummaryRecord:
        return ConversationSummaryRecord(
            id=model.id,
            user_id=model.user_id,
            session_id=model.session_id,
            summary_text=model.summary_text,
            covered_until=model.covered_until,
            created_at=model.created_at,
        )
