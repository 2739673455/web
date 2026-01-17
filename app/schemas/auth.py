from pydantic import BaseModel, Field


class TokenPayload(BaseModel):
    sub: int = Field(..., description="用户 ID")
    scope: str = Field(..., description="权限范围")
    exp: float = Field(..., description="过期时间戳")
    jti: str = Field(..., description="JWT ID")
