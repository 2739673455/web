from typing import Sequence

from app.entities.chat import Conversation, Message
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession


async def get_by_id(
    db_session: AsyncSession, conversation_id: int
) -> Conversation | None:
    """通过 ID 获取对话"""
    return await db_session.get(Conversation, conversation_id)


async def get_by_user_id(
    db_session: AsyncSession, user_id: int
) -> Sequence[Conversation]:
    """通过用户 ID 获取对话列表"""
    stmt = select(Conversation).where(Conversation.user_id == user_id)
    result = await db_session.execute(stmt)
    return result.scalars().all()


async def create(db_session: AsyncSession, user_id: int) -> Conversation:
    """创建对话"""
    conversation = Conversation(user_id=user_id)
    db_session.add(conversation)
    await db_session.commit()
    await db_session.refresh(conversation)
    return conversation


async def modify(
    db_session: AsyncSession, conversation: Conversation, title: str
) -> Conversation:
    """更新对话信息"""
    conversation.title = title
    await db_session.commit()
    await db_session.refresh(conversation)
    return conversation


async def remove(db_session: AsyncSession, conversation_ids: list[int]) -> None:
    """批量删除对话(逻辑删除)，同时删除关联的消息(逻辑删除)"""
    if not conversation_ids:
        return

    # 删除对话
    stmt = (
        update(Conversation).where(Conversation.id.in_(conversation_ids)).values(yn=0)
    )
    await db_session.execute(stmt)

    # 删除关联的消息
    stmt = (
        update(Message)
        .where(Message.conversation_id.in_(conversation_ids))
        .values(yn=0)
    )
    await db_session.execute(stmt)
    await db_session.commit()
