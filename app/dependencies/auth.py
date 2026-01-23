from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Cookie, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, SecurityScopes
from pwdlib._hash import PasswordHash
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.config import CFG
from app.entities.auth import RefreshToken
from app.exceptions.auth import (
    ExpiredAccessTokenError,
    ExpiredRefreshTokenError,
    InsufficientPermissionsError,
    InvalidAccessTokenError,
    InvalidRefreshTokenError,
)
from app.schemas.user import AccessTokenPayload, RefreshTokenPayload

from .database import get_auth_db

password_hash = PasswordHash.recommended()
HASHED_DUMMY_PASSWORD = password_hash.hash("dummy_password")
BEIJING_TZ = timezone(timedelta(hours=8))  # 北京时间时区（UTC+8）


def _authenticate_access_token(token: str) -> AccessTokenPayload:
    """验证访问令牌"""
    try:
        payload = jwt.decode(token, CFG.auth.secret_key, [CFG.auth.algorithm])
        payload["scope"] = payload["scope"].split()
        payload = AccessTokenPayload(**payload)
        return payload
    except jwt.ExpiredSignatureError:
        raise ExpiredAccessTokenError  # 访问令牌过期
    except jwt.exceptions.InvalidTokenError or ValidationError:
        raise InvalidAccessTokenError  # 访问令牌无效


def _authenticate_refresh_token(token: str) -> RefreshTokenPayload:
    """验证刷新令牌"""
    try:
        payload = jwt.decode(token, CFG.auth.secret_key, [CFG.auth.algorithm])
        payload["scope"] = payload["scope"].split()
        payload = RefreshTokenPayload(**payload)
        return payload
    except jwt.ExpiredSignatureError:
        raise ExpiredRefreshTokenError  # 刷新令牌过期
    except jwt.exceptions.InvalidTokenError or ValidationError:
        raise InvalidRefreshTokenError  # 刷新令牌无效


async def _validate_refresh_token_in_db(
    session: AsyncSession, jti: str, user_id: int
) -> None:
    """在数据库中验证刷新令牌"""
    stmt = select(RefreshToken.yn, RefreshToken.expires_at).where(
        RefreshToken.jti == jti, RefreshToken.user_id == user_id
    )
    result = await session.execute(stmt)
    token_record = result.first()

    if not token_record:  # 刷新令牌不存在
        raise InvalidRefreshTokenError
    yn, expires_at = token_record

    if not yn:  # 刷新令牌已被撤销
        raise InvalidRefreshTokenError

    if expires_at.tzinfo is None:  # 确保有时区信息并检查是否过期
        expires_at = expires_at.replace(tzinfo=BEIJING_TZ)
    if datetime.now(BEIJING_TZ) > expires_at:
        raise ExpiredRefreshTokenError  # 刷新令牌过期


async def authenticate_refresh_token(
    refresh_token: Annotated[str, Cookie()],  # 从 Cookie 获取 refresh_token
    session: AsyncSession = Depends(get_auth_db),
) -> RefreshTokenPayload:
    """验证刷新令牌"""
    # 解析刷新令牌
    payload = _authenticate_refresh_token(refresh_token)
    jti, user_id = payload.jti, payload.sub

    # 验证刷新令牌是否在数据库中且未被撤销
    await _validate_refresh_token_in_db(session, jti, user_id)

    return payload


async def authenticate_access_token(
    security_scopes: SecurityScopes,
    credentials: Annotated[
        HTTPAuthorizationCredentials, Depends(HTTPBearer())
    ],  # 从请求头获取 Authorization: Bearer
) -> AccessTokenPayload:
    """验证访问令牌"""
    # 解析访问令牌
    access_token = credentials.credentials
    payload = _authenticate_access_token(access_token)

    # 验证权限范围
    if set(security_scopes.scopes) - set(payload.scope):
        raise InsufficientPermissionsError  # 越权

    return payload
