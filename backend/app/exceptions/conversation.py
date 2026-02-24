"""对话管理异常"""

from app.exceptions.base import NotFoundError


class ConversationNotFoundError(NotFoundError):
    code = 2001
    message = "对话不存在"
