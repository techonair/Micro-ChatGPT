from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ProviderName(str, Enum):
    openai = "openai"
    anthropic = "anthropic"
    llama3 = "llama3"


class ChatRequest(BaseModel):
    user_id: str = Field(min_length=1)
    message: str = Field(min_length=1)
    session_id: str | None = None
    provider: ProviderName = ProviderName.openai
    model: str | None = None


class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float


class ChatResponse(BaseModel):
    session_id: str
    provider: ProviderName
    model: str
    output_text: str
    token_usage: TokenUsage
    timestamp: datetime
