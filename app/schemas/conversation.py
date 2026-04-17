from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.chat import ChatResponse, ProviderName
from app.schemas.history import ConversationSummaryOut, ConversationTurnOut


class ConversationCreateRequest(BaseModel):
    user_id: str = Field(min_length=1)
    message: str = Field(min_length=1)
    provider: ProviderName = ProviderName.openai
    model: str | None = None


class ConversationCreateResponse(BaseModel):
    conversation_id: str
    first_message: ChatResponse


class ConversationMessageRequest(BaseModel):
    user_id: str = Field(min_length=1)
    message: str = Field(min_length=1)
    provider: ProviderName = ProviderName.openai
    model: str | None = None


class ConversationSessionOut(BaseModel):
    conversation_id: str
    started_at: datetime
    updated_at: datetime
    turn_count: int


class ConversationListResponse(BaseModel):
    conversations: list[ConversationSessionOut]


class ConversationDetailResponse(BaseModel):
    conversation_id: str
    turns: list[ConversationTurnOut]
    summaries: list[ConversationSummaryOut]


class ConversationDeleteResponse(BaseModel):
    conversation_id: str
    deleted: bool
