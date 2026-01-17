from datetime import datetime
from pydantic import BaseModel, Field


class CreateConfigRequest(BaseModel):
    model_url: str = Field(..., description="OpenAI 兼容 API URL")
    model_name: str = Field(..., description="模型名称")
    api_key: str = Field(..., description="API 密钥")


class UpdateConfigRequest(BaseModel):
    model_url: str | None = Field(None, description="OpenAI 兼容 API URL")
    model_name: str | None = Field(None, description="模型名称")
    api_key: str | None = Field(None, description="API 密钥")


class ConfigResponse(BaseModel):
    id: int
    model_url: str
    model_name: str
    configured_at: datetime


class ConfigItem(BaseModel):
    id: int
    model_url: str
    model_name: str
    configured_at: datetime


class ConfigListResponse(BaseModel):
    configs: list[ConfigItem]
    total: int