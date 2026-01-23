from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import authenticate_access_token
from app.dependencies.database import get_app_db
from app.schemas.chat import SendMessageRequest
from app.schemas.conversation import (
    ConversationListResponse,
    ConversationResponse,
    CreateConversationRequest,
    DeleteConversationRequest,
)
from app.schemas.user import AccessTokenPayload
from app.services.chat import image_url_to_get_presigned_url
from app.services.conversation import (
    create_conversation,
    delete_conversations,
    generate_title,
    get_conversations,
    update_conversation_title,
)

router = APIRouter(prefix="/conversation", tags=["对话管理"])


@router.get("", response_model=ConversationListResponse)
async def api_get_conversations(
    session: Annotated[AsyncSession, Depends(get_app_db)],
    payload: Annotated[AccessTokenPayload, Depends(authenticate_access_token)],
):
    """获取对话列表"""
    conversations = await get_conversations(session, payload.sub)
    return ConversationListResponse(
        conversations=[
            ConversationResponse(
                conversation_id=i.id, title=i.title, update_at=i.update_at
            )
            for i in conversations
        ]
    )


@router.post(
    "/create", status_code=status.HTTP_201_CREATED, response_model=ConversationResponse
)
async def api_create_conversation(
    request: CreateConversationRequest,
    session: Annotated[AsyncSession, Depends(get_app_db)],
    payload: Annotated[AccessTokenPayload, Depends(authenticate_access_token)],
) -> ConversationResponse:
    """创建新对话"""
    conversation = await create_conversation(
        session, payload.sub, request.model_config_id
    )
    return ConversationResponse(
        conversation_id=conversation.id, title=None, update_at=conversation.update_at
    )


@router.post(
    "/generate_title",
    status_code=status.HTTP_201_CREATED,
    response_model=ConversationResponse,
)
async def api_generate_conversation_title(
    request: SendMessageRequest,
    session: Annotated[AsyncSession, Depends(get_app_db)],
    payload: Annotated[AccessTokenPayload, Depends(authenticate_access_token)],
):
    """生成对话标题"""
    # 转换预签名上传url为预签名下载url
    await image_url_to_get_presigned_url(request.messages)
    # 生成标题
    title = await generate_title(
        request.messages[0].content,
        request.base_url,
        request.model_name,
        request.encrypted_api_key,
    )
    # 更新数据库中的对话标题
    conversation = await update_conversation_title(
        session, request.conversation_id, title
    )
    return ConversationResponse(
        conversation_id=request.conversation_id,
        title=title,
        update_at=conversation.update_at,
    )


@router.post("/delete", status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_conversations(
    request: DeleteConversationRequest,
    session: Annotated[AsyncSession, Depends(get_app_db)],
    payload: Annotated[AccessTokenPayload, Depends(authenticate_access_token)],
):
    """删除对话"""
    await delete_conversations(session, request.ids)
