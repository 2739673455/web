from fastapi import APIRouter, Depends, status
from app.schemas.config import (
    CreateConfigRequest,
    UpdateConfigRequest,
    ConfigResponse,
    ConfigListResponse,
)
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/auth/config", tags=["配置管理"])


@router.get("", response_model=ConfigListResponse)
async def get_configs():
    """获取用户所有模型配置列表 (不含 API 密钥)"""
    # TODO: 实现获取配置列表逻辑
    return ConfigListResponse(
        configs=[
            {
                "id": 1,
                "model_url": "https://api.openai.com/v1",
                "model_name": "gpt-3.5-turbo",
                "configured_at": "2024-01-01T00:00:00Z"
            }
        ],
        total=1
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ConfigResponse)
async def create_config(request: CreateConfigRequest):
    """创建新的模型配置"""
    # TODO: 实现创建配置逻辑
    return ConfigResponse(
        id=1,
        model_url=request.model_url,
        model_name=request.model_name,
        configured_at="2024-01-01T00:00:00Z"
    )


@router.post("/{id}/update", response_model=ConfigResponse)
async def update_config(id: int, request: UpdateConfigRequest):
    """更新指定模型配置"""
    # TODO: 实现更新配置逻辑
    return ConfigResponse(
        id=id,
        model_url=request.model_url or "https://api.openai.com/v1",
        model_name=request.model_name or "gpt-3.5-turbo",
        configured_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z"
    )