from fastapi import APIRouter, Depends, status
from app.schemas.conversation import (
    CreateConversationRequest,
    ConversationResponse,
    ConversationListResponse,
)

router = APIRouter(prefix="/conversations", tags=["对话管理"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ConversationResponse)
async def create_conversation(request: CreateConversationRequest):
    """创建新对话"""
    # TODO: 实现创建对话逻辑
    return ConversationResponse(
        id=1,
        title=request.title or "新对话",
        created_at="2024-01-01T00:00:00Z"
    )


@router.get("", response_model=ConversationListResponse)
async def get_conversations(limit: int = 20, offset: int = 0):
    """获取用户对话列表"""
    # TODO: 实现获取对话列表逻辑
    return ConversationListResponse(
        conversations=[
            {
                "id": 1,
                "title": "对话标题",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "message_count": 5
            }
        ],
        total=10
    )


@router.post("/{id}/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(id: int):
    """删除对话"""
    # TODO: 实现删除对话逻辑
    return None