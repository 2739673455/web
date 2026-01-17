from datetime import datetime
from pydantic import BaseModel, Field


class SendMessageRequest(BaseModel):
    content: str = Field(..., description="用户消息内容")


class MessageResponse(BaseModel):
    id: int
    sender: str
    content: str
    timestamp: datetime


class MessageListResponse(BaseModel):
    messages: list[MessageResponse]
    has_more: bool