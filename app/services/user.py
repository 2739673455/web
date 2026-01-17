from pwdlib._hash import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import create_refresh_token, revoke_refresh_token
from app.entities.auth import Group, User
from app.exceptions.auth import (
    EmailAlreadyExistsError,
    UserEmailSameError,
    UserNameSameError,
    UserNotFoundError,
    UserPasswordSameError,
)
from app.schemas.auth import TokenPayload

password_hash = PasswordHash.recommended()


async def register(
    session: AsyncSession, email: str, username: str, password: str
) -> None:
    """注册新用户"""
    # 检查邮箱是否已存在
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        raise EmailAlreadyExistsError

    # 查找用户组
    group_stmt = select(Group).where(Group.id == 1)
    result = await session.execute(group_stmt)
    group = result.scalar_one_or_none()

    # 创建用户
    user = User(
        email=email,
        name=username,
        password_hash=password_hash.hash(password),
        group=[group],  # 默认加入用户组
    )

    session.add(user)
    await session.commit()


async def login(session: AsyncSession, email: str, password: str) -> dict:
    """用户登录"""
    return await create_refresh_token(session, email, password)


async def get_user(session: AsyncSession, payload: TokenPayload) -> User:
    """获取当前用户信息"""
    stmt = select(User).where(User.id == payload.sub)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise UserNotFoundError
    return user


async def update_username(
    session: AsyncSession, payload: TokenPayload, user_name: str
) -> User:
    """修改用户名"""
    user = await get_user(session, payload)
    if user.name == user_name:
        raise UserNameSameError
    user.name = user_name
    await session.commit()
    return user


async def update_email(
    session: AsyncSession, payload: TokenPayload, email: str
) -> User:
    """修改邮箱"""
    # 检查邮箱是否已被使用
    user = await get_user(session, payload)
    stmt = select(User).where(User.email == email, User.id != user.id)
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        raise EmailAlreadyExistsError
    if user.email == email:
        raise UserEmailSameError
    # 更新邮箱
    user.email = email
    await session.commit()
    return user


async def update_password(
    session: AsyncSession, payload: TokenPayload, password: str
) -> User:
    """修改密码"""
    user = await get_user(session, payload)
    if password_hash.verify(password, user.password_hash):
        raise UserPasswordSameError
    user.password_hash = password_hash.hash(password)
    await session.commit()
    return user


async def logout(session: AsyncSession, payload: TokenPayload):
    """用户登出"""
    await revoke_refresh_token(session, payload)
