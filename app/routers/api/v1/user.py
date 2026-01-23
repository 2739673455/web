from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import (
    authenticate_access_token,
    authenticate_refresh_token,
)
from app.dependencies.database import get_auth_db
from app.schemas.user import (
    AccessTokenPayload,
    LoginRequest,
    LoginResponse,
    RefreshTokenPayload,
    RegisterRequest,
    UpdateEmailRequest,
    UpdatePasswordRequest,
    UpdateUsernameRequest,
    UserResponse,
)
from app.services.auth import create_access_token
from app.services.user import (
    get_user,
    login,
    logout,
    register,
    update_email,
    update_password,
    update_username,
)

router = APIRouter(prefix="/user", tags=["用户管理"])


@router.post("/register", response_model=LoginResponse)
async def api_register(
    request: RegisterRequest,
    session: Annotated[AsyncSession, Depends(get_auth_db)],
) -> LoginResponse:
    """注册新用户"""
    await register(session, request.email, request.username, request.password)
    tokens = await login(session, request.email, request.password)
    return LoginResponse(**tokens)


@router.post("/login", response_model=LoginResponse)
async def api_login(
    request: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_auth_db)],
) -> LoginResponse:
    """用户登录"""
    tokens = await login(session, request.email, request.password)
    return LoginResponse(**tokens)


@router.get("/me", response_model=UserResponse)
async def api_me(
    session: Annotated[AsyncSession, Depends(get_auth_db)],
    payload: Annotated[AccessTokenPayload, Depends(authenticate_access_token)],
) -> UserResponse:
    """获取当前用户信息"""
    user = await get_user(session, payload.sub)
    groups = [g.name for g in user.group]
    return UserResponse(username=user.name, email=user.email, groups=groups)


@router.post("/me/username", status_code=status.HTTP_202_ACCEPTED)
async def api_update_username(
    request: UpdateUsernameRequest,
    session: Annotated[AsyncSession, Depends(get_auth_db)],
    payload: Annotated[AccessTokenPayload, Depends(authenticate_access_token)],
):
    """修改用户名"""
    await update_username(session, payload.sub, request.username)


@router.post("/me/email", status_code=status.HTTP_202_ACCEPTED)
async def api_update_email(
    request: UpdateEmailRequest,
    session: Annotated[AsyncSession, Depends(get_auth_db)],
    payload: Annotated[AccessTokenPayload, Depends(authenticate_access_token)],
):
    """修改邮箱"""
    await update_email(session, payload.sub, request.email)


@router.post("/me/password", response_model=LoginResponse)
async def api_update_password(
    request: UpdatePasswordRequest,
    session: Annotated[AsyncSession, Depends(get_auth_db)],
    payload: Annotated[RefreshTokenPayload, Depends(authenticate_refresh_token)],
) -> LoginResponse:
    """修改密码"""
    await update_password(session, payload.sub, request.password)
    tokens = await create_access_token(session, payload, [])
    return LoginResponse(**tokens)


@router.post("/logout")
async def api_logout(
    session: Annotated[AsyncSession, Depends(get_auth_db)],
    payload: Annotated[RefreshTokenPayload, Depends(authenticate_refresh_token)],
):
    """用户登出"""
    await logout(session, payload)
