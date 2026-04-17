from datetime import datetime

from pydantic import BaseModel, Field


class DocumentCreateRequest(BaseModel):
    title: str | None = None
    content: str = Field(min_length=1)
    metadata: dict[str, str] | None = None


class DocumentResponse(BaseModel):
    id: str
    title: str | None
    content: str
    metadata: dict[str, str] | None
    created_at: datetime
