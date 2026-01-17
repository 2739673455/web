import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Cookie, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, SecurityScopes
from pwdlib._hash import PasswordHash
from pydantic import ValidationError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.config.config import CFG
from app.entities.auth import Group, RefreshToken, User
from app.exceptions.auth import (
    ExpiredTokenError,
    InsufficientPermissionsError,
    InvalidAccessTokenError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    UserDisabledError,
    UserNotFoundError,
)
from app.schemas.auth import TokenPayload

from .database import get_auth_db

password_hash = PasswordHash.recommended()
HASHED_DUMMY_PASSWORD = password_hash.hash("dummy_password")
BEIJING_TZ = timezone(timedelta(hours=8))  # 北京时间时区（UTC+8）


def _generate_refresh_token(user_id: int, scopes: list[str]) -> dict:
    """创建刷新令牌"""
    jti = str(uuid.uuid4())  # JWT ID
    expire = datetime.now(BEIJING_TZ) + timedelta(days=CFG.refresh_token_expire_days)
    payload = {
        "sub": str(user_id),
        "scope": " ".join(scopes),
        "exp": expire.timestamp(),
        "jti": jti,
    }
    token = jwt.encode(payload, CFG.secret_key, CFG.algorithm)
    return {
        "jti": jti,
        "expire": expire,
        "token": token,
    }


def _generate_access_token(jti: str, user_id: int, scopes: list[str]) -> str:
    """创建访问令牌"""
    expire = datetime.now(BEIJING_TZ) + timedelta(
        minutes=CFG.access_token_expire_minutes
    )
    payload = {
        "sub": str(user_id),
        "scope": " ".join(scopes),
        "exp": expire.timestamp(),
        "jti": jti,
    }
    token = jwt.encode(payload, CFG.secret_key, CFG.algorithm)
    return token


def _authenticate_token(token) -> TokenPayload:
    """验证令牌"""
    try:
        # 解码访问令牌
        payload = jwt.decode(token, CFG.secret_key, [CFG.algorithm])
        payload = TokenPayload(**payload)
        return payload
    except jwt.ExpiredSignatureError:
        raise ExpiredTokenError  # 令牌过期
    except jwt.exceptions.InvalidTokenError:
        raise InvalidAccessTokenError  # 令牌无效
    except ValidationError:
        raise InvalidAccessTokenError  # 令牌无效


async def _store_refresh_token_in_db(
    session: AsyncSession, jti: str, user_id: int, expires_at: datetime
) -> None:
    """存储刷新令牌到数据库"""
    refresh_token = RefreshToken(jti=jti, user_id=user_id, expires_at=expires_at)
    session.add(refresh_token)
    await session.commit()


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
    await session.commit()


async def _validate_refresh_token_in_db(
    session: AsyncSession, jti: str, user_id: int
) -> None:
    """在数据库中验证刷新令牌"""
    stmt = select(RefreshToken.yn, RefreshToken.expires_at).where(
        RefreshToken.jti == jti, RefreshToken.user_id == user_id
    )
    result = await session.execute(stmt)
    token_record = result.first()

    if not token_record:
        raise InvalidRefreshTokenError
    yn, expires_at = token_record
    if not yn:
        raise InvalidRefreshTokenError
    if expires_at.tzinfo is None:  # 确保有时区信息并检查是否过期
        expires_at = expires_at.replace(tzinfo=BEIJING_TZ)
    if datetime.now(BEIJING_TZ) > expires_at:
        raise ExpiredTokenError


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

    # 验证密码（使用 dummy_password 避免时间攻击）
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


async def revoke_refresh_token(session: AsyncSession, payload: TokenPayload) -> None:
    """撤销刷新令牌"""
    jti, user_id = payload.jti, payload.sub
    # 撤销旧的刷新令牌
    await _revoke_refresh_token_in_db(session, jti, user_id)


async def create_access_token(
    session: AsyncSession, payload: TokenPayload, scopes: list[str]
) -> dict:
    """创建访问令牌,同时刷新刷新令牌"""
    jti, user_id, payload_scope = payload.jti, payload.sub, payload.scope
    # 验证权限范围
    refresh_token_scopes = payload_scope.split()
    # 如果没有选择权限，默认使用用户拥有的所有权限
    scopes = scopes if scopes else refresh_token_scopes
    if set(scopes) - set(refresh_token_scopes):
        raise InsufficientPermissionsError

    # 撤销旧的刷新令牌
    await _revoke_refresh_token_in_db(session, jti, user_id)
    # 生成新的刷新令牌
    _rt = _generate_refresh_token(user_id, refresh_token_scopes)
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


async def authenticate_refresh_token(
    refresh_token: Annotated[str, Cookie()],  # 从 Cookie 获取 refresh_token
    session: AsyncSession = Depends(get_auth_db),
) -> TokenPayload:
    """验证刷新令牌"""
    # 解析刷新令牌
    payload = _authenticate_token(refresh_token)
    jti, user_id = payload.jti, payload.sub

    # 验证刷新令牌是否在数据库中且未被撤销
    await _validate_refresh_token_in_db(session, jti, user_id)

    return payload


async def authenticate_access_token(
    security_scopes: SecurityScopes,
    credentials: Annotated[
        HTTPAuthorizationCredentials, Depends(HTTPBearer())
    ],  # 从请求头获取 Authorization: Bearer
) -> TokenPayload:
    """验证访问令牌"""
    # 解析访问令牌
    access_token = credentials.credentials
    payload = _authenticate_token(access_token)
    scope = payload.scope

    # 验证权限范围
    token_scopes = scope.split()
    if set(security_scopes.scopes) - set(token_scopes):
        raise InsufficientPermissionsError  # 越权

    return payload
