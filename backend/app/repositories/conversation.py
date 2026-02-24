from typing import Sequence

from app.entities.chat import Conversation
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_by_user_id(
    db_session: AsyncSession, user_id: int
) -> Sequence[Conversation]:
    """通过用户 ID 获取对话列表"""
    stmt = select(Conversation).where(Conversation.user_id == user_id)
    result = await db_session.execute(stmt)
    return result.scalars().all()


async def create(
    db_session: AsyncSession, user_id: int, model_config_id: int
) -> Conversation:
    """创建对话"""
    conversation = Conversation(user_id=user_id, model_config_id=model_config_id)
    db_session.add(conversation)
    await db_session.commit()
    await db_session.refresh(conversation)
    return conversation


async def update():
    """更新对话信息"""


async def remove():
    """批量删除对话(逻辑删除)，同时删除关联的消息(逻辑删除)"""
