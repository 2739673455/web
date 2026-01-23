from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.exceptions.auth import (
    ExpiredAccessTokenError,
    InsufficientPermissionsError,
    InvalidAccessTokenError,
    InvalidRefreshTokenError,
)


def register_auth_exception_handlers(app):
    @app.exception_handler(ExpiredAccessTokenError)
    async def expired_token_handler(request: Request, exc: ExpiredAccessTokenError):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": str(exc)},
        )

    @app.exception_handler(InsufficientPermissionsError)
    async def insufficient_permissions_handler(
        request: Request, exc: InsufficientPermissionsError
    ):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": str(exc)},
        )

    @app.exception_handler(InvalidAccessTokenError)
    async def invalid_access_token_handler(
        request: Request, exc: InvalidAccessTokenError
    ):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": str(exc)},
        )

    @app.exception_handler(InvalidRefreshTokenError)
    async def invalid_refresh_token_handler(
        request: Request, exc: InvalidRefreshTokenError
    ):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": str(exc)},
        )
