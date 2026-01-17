from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class CreateConversationRequest(BaseModel):
    title: Optional[str] = Field(None, description="对话标题")


class ConversationResponse(BaseModel):
    id: int
    title: str
    created_at: datetime


class ConversationItem(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int


class ConversationListResponse(BaseModel):
    conversations: list[ConversationItem]
    total: int