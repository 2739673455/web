from typing import Sequence

from app.entities.chat import Message
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_by_conversation_id(
    db_session: AsyncSession, conversation_id: int
) -> Sequence[Message]:
    """通过对话 ID 获取消息列表"""
    stmt = select(Message).where(Message.conversation_id == conversation_id)
    result = await db_session.execute(stmt)
    return result.scalars().all()
