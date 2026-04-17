from datetime import datetime

from pydantic import BaseModel


class ConversationTurnOut(BaseModel):
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


class ConversationSummaryOut(BaseModel):
    id: str
    user_id: str
    session_id: str
    summary_text: str
    covered_until: datetime
    created_at: datetime


class HistoryResponse(BaseModel):
    turns: list[ConversationTurnOut]
    summaries: list[ConversationSummaryOut]
