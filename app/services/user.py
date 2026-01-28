from pwdlib._hash import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager

from app.entities.auth import Group, User
from app.exceptions.user import (
    EmailAlreadyExistsError,
    UserEmailSameError,
    UserNameSameError,
    UserNotFoundError,
    UserPasswordSameError,
)

password_hash = PasswordHash.recommended()


async def verify_email_exists(db_session: AsyncSession, email: str) -> None:
    """验证邮箱是否已存在"""
    stmt = select(User).where(User.email == email)
    result = await db_session.execute(stmt)
    if result.scalar_one_or_none():
        raise EmailAlreadyExistsError


async def get_default_group(db_session: AsyncSession) -> Group | None:
    """获取默认组"""
    stmt = select(Group).where(Group.id == 1, Group.yn == 1)
    result = await db_session.execute(stmt)
    return result.scalar_one_or_none()


async def add_user_in_db(
    db_session: AsyncSession,
    email: str,
    username: str,
    password: str,
    groups: list[Group],
) -> User:
    """将用户加入数据库"""
    try:
        # 创建用户
        user = User(
            email=email,
            name=username,
            password_hash=password_hash.hash(password),
            group=groups,
        )
        # 添加用户
        db_session.add(user)
        await db_session.commit()
        return user
    except Exception:
        await db_session.rollback()
        raise


async def get_user(db_session: AsyncSession, user_id: int) -> User:
    """获取当前用户信息"""
    stmt = (
        select(User)
        .join(Group, User.group)
        .options(contains_eager(User.group))
        .where(User.id == user_id, Group.yn == 1)
    )
    result = await db_session.execute(stmt)
    user = result.unique().scalar_one_or_none()
    if not user:
        raise UserNotFoundError
    return user


async def update_username(
    db_session: AsyncSession, user_id: int, user_name: str
) -> None:
    """修改用户名"""
    user = await get_user(db_session, user_id)
    if user.name == user_name:
        raise UserNameSameError
    # 更新用户名
    user.name = user_name
    try:
        await db_session.commit()
    except Exception:
        await db_session.rollback()
        raise


async def update_email(db_session: AsyncSession, user_id: int, email: str) -> None:
    """修改邮箱"""
    # 检查邮箱是否已被使用
    user = await get_user(db_session, user_id)
    stmt = select(User).where(User.email == email, User.id != user.id)
    result = await db_session.execute(stmt)
    if result.scalar_one_or_none():
        raise EmailAlreadyExistsError
    if user.email == email:
        raise UserEmailSameError
    # 更新邮箱
    user.email = email
    try:
        await db_session.commit()
    except Exception:
        await db_session.rollback()
        raise


async def update_password(
    db_session: AsyncSession, user_id: int, password: str
) -> None:
    """修改密码"""
    user = await get_user(db_session, user_id)
    if password_hash.verify(password, user.password_hash):
        raise UserPasswordSameError
    # 更新密码
    user.password_hash = password_hash.hash(password)
    try:
        await db_session.commit()
    except Exception:
        await db_session.rollback()
        raise
