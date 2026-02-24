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
