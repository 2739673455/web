from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import (
    authenticate_access_token,
    authenticate_refresh_token,
    create_access_token,
)
from app.dependencies.database import get_auth_db
from app.schemas.auth import TokenPayload
from app.schemas.user import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    UpdateEmailRequest,
    UpdatePasswordRequest,
    UpdateUsernameRequest,
    UserResponse,
)
from app.services.user import (
    get_user,
    login,
    logout,
    register,
    update_email,
    update_password,
    update_username,
)

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=LoginResponse)
async def api_register(
    req: Request, request: RegisterRequest, session: AsyncSession = Depends(get_auth_db)
) -> LoginResponse:
    """注册新用户"""
    # client_ip = req.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    # if not client_ip:
    #     client_ip = getattr(req.client, "host", "unknown")
    await register(session, request.email, request.username, request.password)
    tokens = await login(session, request.email, request.password)
    return LoginResponse(**tokens)


@router.post("/login", response_model=LoginResponse)
async def api_login(
    request: LoginRequest, session: AsyncSession = Depends(get_auth_db)
) -> LoginResponse:
    """用户登录"""
    tokens = await login(session, request.email, request.password)
    return LoginResponse(**tokens)


@router.get("/me", response_model=UserResponse)
async def api_me(
    payload: Annotated[TokenPayload, Depends(authenticate_access_token)],
    session: AsyncSession = Depends(get_auth_db),
) -> UserResponse:
    """获取当前用户信息"""
    user = await get_user(session, payload)
    return UserResponse(user_id=user.id, email=user.email, username=user.name)


@router.post("/me/username", response_model=UserResponse)
async def api_update_username(
    request: UpdateUsernameRequest,
    payload: Annotated[TokenPayload, Depends(authenticate_access_token)],
    session: AsyncSession = Depends(get_auth_db),
) -> UserResponse:
    """修改用户名"""
    user = await update_username(session, payload, request.username)
    return UserResponse(user_id=user.id, email=user.email, username=user.name)


@router.post("/me/email", response_model=UserResponse)
async def api_update_email(
    request: UpdateEmailRequest,
    payload: Annotated[TokenPayload, Depends(authenticate_access_token)],
    session: AsyncSession = Depends(get_auth_db),
) -> UserResponse:
    """修改邮箱"""
    user = await update_email(session, payload, request.email)
    return UserResponse(user_id=user.id, email=user.email, username=user.name)


@router.post("/me/password", response_model=LoginResponse)
async def api_update_password(
    request: UpdatePasswordRequest,
    payload: Annotated[TokenPayload, Depends(authenticate_refresh_token)],
    session: AsyncSession = Depends(get_auth_db),
) -> LoginResponse:
    """修改密码"""
    await update_password(session, payload, request.password)
    tokens = await create_access_token(session, payload, [])
    return LoginResponse(**tokens)


@router.post("/logout")
async def api_logout(
    payload: Annotated[TokenPayload, Depends(authenticate_refresh_token)],
    session: AsyncSession = Depends(get_auth_db),
):
    """用户登出"""
    await logout(session, payload)
