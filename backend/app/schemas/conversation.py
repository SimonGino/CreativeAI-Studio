from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ConversationCreate(BaseModel):
    title: str = "New Conversation"


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    role: str = "user"
    content: str
    media_type: str | None = None
    media_url: str | None = None
    model: str | None = None
    config: dict | None = None


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    media_type: str | None = None
    media_url: str | None = None
    model: str | None = None
    config: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationDetailResponse(ConversationResponse):
    messages: list[MessageResponse] = []
