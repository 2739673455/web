from datetime import datetime

from pydantic import BaseModel, Field


class TextContent(BaseModel):
    type: str = "text"
    text: str = Field(..., description="文本内容")

    def to_dict(self):
        return {"type": self.type, "text": self.text}


class ImageContent(BaseModel):
    type: str = "image_url"
    image_url: str = Field(..., description="图片链接")

    def to_dict(self):
        return {"type": self.type, "image_url": self.image_url}


class Attachment(BaseModel):
    name: str = Field(..., description="附件名称")
    url: str = Field(..., description="附件链接")


class MessageItem(BaseModel):
    message_id: int | None = Field(default=None, description="消息ID")
    role: str = Field(..., description="发送者 (user/assistant/tool)")
    content: str | list[TextContent | ImageContent] = Field(..., description="消息内容")
    attachments: list[Attachment] | None = Field(default=None, description="附件列表")
    create_at: datetime | None = Field(default=None, description="发送时间")


class SendMessageRequest(BaseModel):
    conversation_id: int = Field(..., description="对话ID")
    messages: list[MessageItem] = Field(..., description="消息列表")
    model_code: str = Field(..., description="模型代码")


class MessageListResponse(BaseModel):
    messages: list[MessageItem]


class ConversationTitleResponse(BaseModel):
    title: str
