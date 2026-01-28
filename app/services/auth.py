import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Cookie, Depends, Header
from fastapi.security import SecurityScopes
from pwdlib._hash import PasswordHash
from pydantic import ValidationError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.config.config import CFG
from app.entities.auth import Group, RefreshToken, User
from app.exceptions.auth import (
    ExpiredAccessTokenError,
    ExpiredRefreshTokenError,
    InsufficientPermissionsError,
    InvalidAccessTokenError,
    InvalidRefreshTokenError,
)
from app.exceptions.user import (
    InvalidCredentialsError,
    UserDisabledError,
    UserNotFoundError,
)
from app.schemas.user import AccessTokenPayload, RefreshTokenPayload
from app.services.database import get_auth_db
from app.utils.context import user_id_ctx

password_hash = PasswordHash.recommended()
HASHED_DUMMY_PASSWORD = password_hash.hash("dummy_password")
BEIJING_TZ = timezone(timedelta(hours=8))  # 北京时间时区（UTC+8）


def _generate_refresh_token(user_id: int, scopes: list[str]) -> dict:
    """创建刷新令牌"""
    jti = str(uuid.uuid4())  # JWT ID
    expire = datetime.now(BEIJING_TZ) + timedelta(
        days=CFG.auth.refresh_token_expire_days
    )  # 刷新令牌过期时间
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
    )  # 访问令牌过期时间
    payload = {
        "sub": str(user_id),
        "scope": " ".join(scopes),
        "exp": expire.timestamp(),
        "jti": jti,
    }
    token = jwt.encode(payload, CFG.auth.secret_key, CFG.auth.algorithm)
    return token


async def _store_refresh_token_in_db(
    db_session: AsyncSession, jti: str, user_id: int, expires_at: datetime
) -> None:
    """存储刷新令牌到数据库"""
    refresh_token = RefreshToken(jti=jti, user_id=user_id, expires_at=expires_at)
    db_session.add(refresh_token)
    try:
        await db_session.commit()
    except Exception:
        await db_session.rollback()
        raise


async def _authenticate_user(
    db_session: AsyncSession, email: str, password: str
) -> dict:
    """验证邮箱和密码"""
    # 查询用户信息及其权限
    stmt = (
        select(User)
        .options(joinedload(User.group).joinedload(Group.scope))
        .where(User.email == email)
    )
    result = await db_session.execute(stmt)
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

    return {"user_id": user.id, "scopes": scopes}


async def create_token(db_session: AsyncSession, email: str, password: str) -> dict:
    """创建刷新令牌和访问令牌"""
    # 验证邮箱、密码
    user = await _authenticate_user(db_session, email, password)
    user_id, scopes = user["user_id"], user["scopes"]

    # 创建刷新令牌
    _rt = _generate_refresh_token(user_id, scopes)
    jti, expire, r_token = _rt["jti"], _rt["expire"], _rt["token"]
    # 存储刷新令牌
    await _store_refresh_token_in_db(db_session, jti, user_id, expire)

    # 创建访问令牌
    a_token = _generate_access_token(jti, user_id, scopes)

    return {
        "user_id": user_id,
        "access_token": a_token,
        "refresh_token": r_token,
        "token_type": "bearer",
    }


async def revoke_refresh_token(
    db_session: AsyncSession, jti: str, user_id: int
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
    await db_session.execute(stmt)
    try:
        await db_session.commit()
    except Exception:
        await db_session.rollback()
        raise


async def refresh_token(
    db_session: AsyncSession, payload: RefreshTokenPayload, scopes: list[str]
) -> dict:
    """刷新刷新令牌和访问令牌"""
    jti, user_id, payload_scope = payload.jti, payload.sub, payload.scope
    # 如果没有选择权限，默认使用该用户所有权限
    scopes = scopes if scopes else payload_scope
    # 验证权限范围
    if set(scopes) - set(payload_scope):
        raise InsufficientPermissionsError

    # 撤销旧的刷新令牌
    await revoke_refresh_token(db_session, jti, user_id)
    # 生成新的刷新令牌
    _rt = _generate_refresh_token(user_id, payload_scope)
    jti, expire, r_token = _rt["jti"], _rt["expire"], _rt["token"]
    # 存储新的刷新令牌
    await _store_refresh_token_in_db(db_session, jti, user_id, expire)

    # 创建访问令牌
    a_token = _generate_access_token(jti, user_id, scopes)

    return {
        "access_token": a_token,
        "refresh_token": r_token,
        "token_type": "bearer",
    }


async def revoke_all_refresh_tokens(db_session: AsyncSession, user_id: int) -> None:
    """撤销用户的所有刷新令牌"""
    stmt = (
        update(RefreshToken)
        .where(
            RefreshToken.user_id == user_id,
            RefreshToken.yn == 1,
        )
        .values(yn=0)
    )
    try:
        await db_session.execute(stmt)
        await db_session.commit()
    except:
        await db_session.rollback()
        raise


def _verify_access_token(token: str) -> AccessTokenPayload:
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


def _get_access_token(
    authorization: Annotated[str | None, Header()] = None,  # 从请求头获取 Bearer token
) -> str | None:
    """从请求头获取 Bearer token"""
    if authorization is None:
        raise InvalidAccessTokenError
    return authorization.replace("Bearer ", "")


async def authenticate_access_token(
    access_token: Annotated[str, Depends(_get_access_token)],
    security_scopes: SecurityScopes,
) -> AccessTokenPayload:
    """验证访问令牌"""
    payload = _verify_access_token(access_token)
    user_id, scopes = payload.sub, payload.scope

    # 设置 user_id 到 ContextVar
    user_id_ctx.set(str(user_id))

    # 验证权限范围
    if set(security_scopes.scopes) - set(scopes):
        raise InsufficientPermissionsError  # 越权

    return payload


async def _validate_refresh_token_in_db(
    db_session: AsyncSession, jti: str, user_id: int
) -> None:
    """在数据库中验证刷新令牌"""
    stmt = select(RefreshToken.yn, RefreshToken.expires_at).where(
        RefreshToken.jti == jti, RefreshToken.user_id == user_id
    )
    result = await db_session.execute(stmt)
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


def _verify_refresh_token(token: str) -> RefreshTokenPayload:
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


async def authenticate_refresh_token(
    refresh_token: Annotated[str, Cookie()],  # 从 Cookie 获取 refresh_token
    db_session: Annotated[AsyncSession, Depends(get_auth_db)],
) -> RefreshTokenPayload:
    """验证刷新令牌"""
    # 解析刷新令牌
    payload = _verify_refresh_token(refresh_token)
    jti, user_id = payload.jti, payload.sub

    # 设置 user_id 到 ContextVar
    user_id_ctx.set(str(user_id))

    # 验证刷新令牌是否在数据库中且未被撤销
    await _validate_refresh_token_in_db(db_session, jti, user_id)

    return payload
