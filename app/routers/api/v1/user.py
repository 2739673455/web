from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
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
from app.services.auth import (
    create_token,
    refresh_token,
    revoke_all_refresh_tokens,
    revoke_refresh_token,
)
from app.services.user import (
    get_user,
    register,
    update_email,
    update_password,
    update_username,
)
from app.utils.context import user_id_ctx
from app.utils.log import auth_logger

router = APIRouter(prefix="/user", tags=["用户管理"])


@router.post("/register", response_model=LoginResponse)
async def api_register(
    request: RegisterRequest,
    db_session: Annotated[AsyncSession, Depends(get_auth_db)],
    response: Response,
) -> LoginResponse:
    """注册新用户"""
    await register(db_session, request.email, request.username, request.password)
    result = await create_token(db_session, request.email, request.password)
    user_id_ctx.set(str(result["user_id"]))  # 设置 user_id 到 ContextVar
    auth_logger.info("User register")
    # 设置 refresh_token cookie
    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,  # 防止 JavaScript 访问 cookie
        secure=False,
        samesite="lax",
    )
    return LoginResponse(**result)


@router.post("/login", response_model=LoginResponse)
async def api_login(
    request: LoginRequest,
    db_session: Annotated[AsyncSession, Depends(get_auth_db)],
    response: Response,
) -> LoginResponse:
    """用户登录"""
    result = await create_token(db_session, request.email, request.password)
    user_id_ctx.set(str(result["user_id"]))  # 设置 user_id 到 ContextVar
    auth_logger.info("User login")
    # 设置 refresh_token cookie
    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,  # 防止 JavaScript 访问 cookie
        secure=False,
        samesite="lax",
    )
    return LoginResponse(**result)


@router.post("/refresh", response_model=LoginResponse)
async def api_refresh(
    db_session: Annotated[AsyncSession, Depends(get_auth_db)],
    payload: Annotated[RefreshTokenPayload, Depends(authenticate_refresh_token)],
) -> LoginResponse:
    """刷新令牌"""
    auth_logger.info("User refresh token")
    tokens = await refresh_token(db_session, payload, [])
    return LoginResponse(**tokens)


@router.get("/me", response_model=UserResponse)
async def api_me(
    db_session: Annotated[AsyncSession, Depends(get_auth_db)],
    payload: Annotated[AccessTokenPayload, Depends(authenticate_access_token)],
) -> UserResponse:
    """获取当前用户信息"""
    auth_logger.info("User get user info")
    user = await get_user(db_session, payload.sub)
    groups = [g.name for g in user.group]
    return UserResponse(username=user.name, email=user.email, groups=groups)


@router.post("/me/username", status_code=status.HTTP_202_ACCEPTED)
async def api_update_username(
    request: UpdateUsernameRequest,
    db_session: Annotated[AsyncSession, Depends(get_auth_db)],
    payload: Annotated[AccessTokenPayload, Depends(authenticate_access_token)],
):
    """修改用户名"""
    auth_logger.info("User update username")
    await update_username(db_session, payload.sub, request.username)


@router.post("/me/email", status_code=status.HTTP_202_ACCEPTED)
async def api_update_email(
    request: UpdateEmailRequest,
    db_session: Annotated[AsyncSession, Depends(get_auth_db)],
    payload: Annotated[RefreshTokenPayload, Depends(authenticate_refresh_token)],
    response: Response,
):
    """修改邮箱"""
    auth_logger.info("User update email")
    # 修改邮箱
    await update_email(db_session, payload.sub, request.email)
    # 撤销该用户的所有历史刷新令牌
    await revoke_all_refresh_tokens(db_session, payload.sub)
    auth_logger.info(f"User {payload.sub} password updated, all refresh tokens revoked")
    # 生成新的访问令牌和刷新令牌
    tokens = await refresh_token(db_session, payload, [])
    # 设置新的 refresh_token cookie
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        secure=False,
        samesite="lax",
    )
    return LoginResponse(
        **tokens
    )  # TODO 后端修改邮箱改为使用刷新令牌，返回刷新令牌和访问令牌


@router.post("/me/password", response_model=LoginResponse)
async def api_update_password(
    request: UpdatePasswordRequest,
    db_session: Annotated[AsyncSession, Depends(get_auth_db)],
    payload: Annotated[RefreshTokenPayload, Depends(authenticate_refresh_token)],
    response: Response,
) -> LoginResponse:
    """修改密码"""
    auth_logger.info("User update password")
    # 验证并修改密码
    await update_password(db_session, payload.sub, request.password)
    # 撤销该用户的所有历史刷新令牌
    await revoke_all_refresh_tokens(db_session, payload.sub)
    auth_logger.info(f"User {payload.sub} password updated, all refresh tokens revoked")
    # 生成新的访问令牌和刷新令牌
    tokens = await refresh_token(db_session, payload, [])
    # 设置新的 refresh_token cookie
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        secure=False,
        samesite="lax",
    )
    return LoginResponse(**tokens)


@router.post("/logout")
async def api_logout(
    db_session: Annotated[AsyncSession, Depends(get_auth_db)],
    payload: Annotated[RefreshTokenPayload, Depends(authenticate_refresh_token)],
):
    """用户登出"""
    auth_logger.info("User logout")
    await revoke_refresh_token(db_session, payload.jti, payload.sub)
