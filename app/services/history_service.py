from app.repositories.conversations.base import ConversationRepository
from app.schemas.history import ConversationSummaryOut, ConversationTurnOut, HistoryResponse


class HistoryService:
    def __init__(self, repo: ConversationRepository) -> None:
        self.repo = repo

    async def get_history(self, *, user_id: str, session_id: str | None = None) -> HistoryResponse:
        turns = await self.repo.list_turns(user_id=user_id, session_id=session_id, limit=200)
        summaries = await self.repo.list_summaries(user_id=user_id, session_id=session_id, limit=50)

        return HistoryResponse(
            turns=[ConversationTurnOut(**t.__dict__) for t in turns],
            summaries=[ConversationSummaryOut(**s.__dict__) for s in summaries],
        )
