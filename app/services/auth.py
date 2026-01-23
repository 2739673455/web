import uuid
from datetime import datetime, timedelta

import jwt
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.config.config import CFG
from app.dependencies.auth import BEIJING_TZ, HASHED_DUMMY_PASSWORD, password_hash
from app.entities.auth import Group, RefreshToken, User
from app.exceptions.auth import InsufficientPermissionsError
from app.exceptions.user import (
    InvalidCredentialsError,
    UserDisabledError,
    UserNotFoundError,
)
from app.schemas.user import RefreshTokenPayload


def _generate_refresh_token(user_id: int, scopes: list[str]) -> dict:
    """创建刷新令牌"""
    jti = str(uuid.uuid4())  # JWT ID
    expire = datetime.now(BEIJING_TZ) + timedelta(
        days=CFG.auth.refresh_token_expire_days
    )
    payload = {
        "sub": str(user_id),
        "scope": " ".join(scopes),
        "exp": expire.timestamp(),
        "jti": jti,
    }
    token = jwt.encode(payload, CFG.auth.secret_key, CFG.auth.algorithm)
    return {
        "jti": jti,
        "expire": expire,
        "token": token,
    }


def _generate_access_token(jti: str, user_id: int, scopes: list[str]) -> str:
    """创建访问令牌"""
    expire = datetime.now(BEIJING_TZ) + timedelta(
        minutes=CFG.auth.access_token_expire_minutes
    )
    payload = {
        "sub": str(user_id),
        "scope": " ".join(scopes),
        "exp": expire.timestamp(),
    }
    token = jwt.encode(payload, CFG.auth.secret_key, CFG.auth.algorithm)
    return token


async def _store_refresh_token_in_db(
    session: AsyncSession, jti: str, user_id: int, expires_at: datetime
) -> None:
    """存储刷新令牌到数据库"""
    refresh_token = RefreshToken(jti=jti, user_id=user_id, expires_at=expires_at)
    session.add(refresh_token)
    try:
        await session.commit()
    except Exception:
        await session.rollback()
        raise


async def _revoke_refresh_token_in_db(
    session: AsyncSession, jti: str, user_id: int
) -> None:
    """在数据库中撤销刷新令牌"""
    stmt = (
        update(RefreshToken)
        .where(
            RefreshToken.jti == jti,
            RefreshToken.user_id == user_id,
            RefreshToken.yn == 1,
        )
        .values(yn=0)
    )
    await session.execute(stmt)
    try:
        await session.commit()
    except Exception:
        await session.rollback()
        raise


async def _authenticate_user(session: AsyncSession, email: str, password: str) -> dict:
    """验证邮箱和密码"""
    # 查询用户信息及其权限
    stmt = (
        select(User)
        .options(joinedload(User.group).joinedload(Group.scope))
        .where(User.email == email)
    )
    result = await session.execute(stmt)
    user = result.unique().scalar_one_or_none()
    if not user:
        raise UserNotFoundError  # 用户不存在
    if not user.yn:
        raise UserDisabledError  # 用户禁用

    # 验证密码（使用 dummy_password 避免时序攻击）
    target_hash = user.password_hash if user else HASHED_DUMMY_PASSWORD
    password_correct = password_hash.verify(password, target_hash)
    if not password_correct:
        raise InvalidCredentialsError  # 邮箱或密码错误

    # 收集可用权限
    scopes = [
        scope.name
        for group in user.group
        if group.yn
        for scope in group.scope
        if scope.yn
    ]

    return {"id": user.id, "scopes": scopes}


async def create_refresh_token(
    session: AsyncSession, email: str, password: str
) -> dict:
    """创建刷新令牌和访问令牌"""
    # 验证邮箱、密码
    user = await _authenticate_user(session, email, password)
    user_id, scopes = user["id"], user["scopes"]

    # 创建刷新令牌
    _rt = _generate_refresh_token(user_id, scopes)
    jti, expire, r_token = _rt["jti"], _rt["expire"], _rt["token"]
    # 存储刷新令牌
    await _store_refresh_token_in_db(session, jti, user_id, expire)

    # 创建访问令牌
    a_token = _generate_access_token(jti, user_id, scopes)

    return {
        "access_token": a_token,
        "refresh_token": r_token,
        "token_type": "bearer",
    }


async def create_access_token(
    session: AsyncSession, payload: RefreshTokenPayload, scopes: list[str]
) -> dict:
    """创建访问令牌,同时刷新刷新令牌"""
    jti, user_id, payload_scope = payload.jti, payload.sub, payload.scope
    # 如果没有选择权限，默认使用该用户所有权限
    scopes = scopes if scopes else payload_scope
    # 验证权限范围
    if set(scopes) - set(payload_scope):
        raise InsufficientPermissionsError

    # 撤销旧的刷新令牌
    await _revoke_refresh_token_in_db(session, jti, user_id)
    # 生成新的刷新令牌
    _rt = _generate_refresh_token(user_id, payload_scope)
    jti, expire, r_token = _rt["jti"], _rt["expire"], _rt["token"]
    # 存储新的刷新令牌
    await _store_refresh_token_in_db(session, jti, user_id, expire)

    # 创建访问令牌
    a_token = _generate_access_token(jti, user_id, scopes)

    return {
        "access_token": a_token,
        "refresh_token": r_token,
        "token_type": "bearer",
    }


async def revoke_refresh_token(
    session: AsyncSession, payload: RefreshTokenPayload
) -> None:
    """撤销刷新令牌"""
    jti, user_id = payload.jti, payload.sub
    # 撤销旧的刷新令牌
    await _revoke_refresh_token_in_db(session, jti, user_id)
