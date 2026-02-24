from typing import Sequence

from app.entities.chat import Message
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession


async def get_by_conversation_id(
    db_session: AsyncSession, conversation_id: int
) -> Sequence[Message]:
    """通过对话 ID 获取消息列表"""
    stmt = select(Message).where(Message.conversation_id == conversation_id)
    result = await db_session.execute(stmt)
    return result.scalars().all()


async def create(
    db_session: AsyncSession, conversation_id: int, role: str, content: str
) -> Message:
    """创建消息"""
    message = Message(conversation_id=conversation_id, role=role, content=content)
    db_session.add(message)
    await db_session.commit()
    await db_session.refresh(message)
    return message


async def remove(db_session: AsyncSession, message_ids: list[int]) -> None:
    """批量删除消息(逻辑删除)"""
    if not message_ids:
        return

    stmt = update(Message).where(Message.id.in_(message_ids)).values(yn=0)
    await db_session.execute(stmt)
    await db_session.commit()
