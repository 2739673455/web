from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="邮箱")
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=128, description="密码")


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., description="密码")


class UpdateUsernameRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="新用户名")


class UpdateEmailRequest(BaseModel):
    email: EmailStr = Field(..., description="新邮箱")


class UpdatePasswordRequest(BaseModel):
    password: str = Field(..., min_length=6, max_length=128, description="新密码")


class UserResponse(BaseModel):
    user_id: int
    email: EmailStr
    username: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
