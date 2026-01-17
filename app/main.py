from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.config.config import CFG
from app.exceptions.auth import (
    EmailAlreadyExistsError,
    ExpiredTokenError,
    InsufficientPermissionsError,
    InvalidAccessTokenError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    UserDisabledError,
    UserEmailSameError,
    UserNameSameError,
    UserNotFoundError,
    UserPasswordSameError,
)
from app.routers import chat, config, conversations, user

app = FastAPI()


@app.exception_handler(InvalidCredentialsError)
async def invalid_credentials_handler(request: Request, exc: InvalidCredentialsError):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": str(exc)},
    )


@app.exception_handler(UserNotFoundError)
async def user_not_found_handler(request: Request, exc: UserNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": str(exc)},
    )


@app.exception_handler(UserDisabledError)
async def user_disabled_handler(request: Request, exc: UserDisabledError):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": str(exc)},
    )


@app.exception_handler(ExpiredTokenError)
async def expired_token_handler(request: Request, exc: ExpiredTokenError):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": str(exc)},
    )


@app.exception_handler(InvalidAccessTokenError)
async def invalid_access_token_handler(request: Request, exc: InvalidAccessTokenError):
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


@app.exception_handler(InsufficientPermissionsError)
async def insufficient_permissions_handler(
    request: Request, exc: InsufficientPermissionsError
):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": str(exc)},
    )


@app.exception_handler(EmailAlreadyExistsError)
async def email_already_exists_handler(request: Request, exc: EmailAlreadyExistsError):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


@app.exception_handler(UserEmailSameError)
async def user_email_same_handler(request: Request, exc: UserEmailSameError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


@app.exception_handler(UserNameSameError)
async def user_name_same_handler(request: Request, exc: UserNameSameError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


@app.exception_handler(UserPasswordSameError)
async def user_password_same_handler(request: Request, exc: UserPasswordSameError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


app.include_router(user.router)
app.include_router(config.router)
app.include_router(conversations.router)
app.include_router(chat.router)


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=CFG.port)
