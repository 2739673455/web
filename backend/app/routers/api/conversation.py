from typing import Annotated

from app.exceptions import conversation as conversation_error
from app.repositories import conversation as conversation_repo
from app.schemas import conversation as conversation_schema
from app.utils import db
from fastapi import APIRouter, Depends, Request, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/conversation", tags=["对话管理"])


@router.get("/list")
async def api_list_conversations(
    request: Request, db_session: Annotated[AsyncSession, Depends(db.get_app_db)]
) -> conversation_schema.ConversationListResponse:
    """获取对话列表"""
    payload = request.state.payload
    conversations = await conversation_repo.get_by_user_id(db_session, payload.sub)
    logger.info(
        f"User get conversations: conversations={[i.id for i in conversations]}"
    )
    return conversation_schema.ConversationListResponse(
        conversations=[
            conversation_schema.ConversationResponse(
                conversation_id=i.id, title=i.title, update_at=i.update_at
            )
            for i in conversations
        ]
    )


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def api_create_conversation(
    request: Request, db_session: Annotated[AsyncSession, Depends(db.get_app_db)]
) -> conversation_schema.ConversationResponse:
    """创建新对话"""
    payload = request.state.payload
    conversation = await conversation_repo.create(db_session, payload.sub)
    logger.info(f"User create conversation: conversation_id={conversation.id}")
    return conversation_schema.ConversationResponse(
        conversation_id=conversation.id, title=None, update_at=conversation.update_at
    )


@router.post("/update")
async def api_update_conversation(
    body: conversation_schema.UpdateConversationRequest,
    db_session: Annotated[AsyncSession, Depends(db.get_app_db)],
) -> None:
    """修改对话信息"""
    logger.info(f"User update conversation: conversation_id={body.conversation_id}")
    conversation = await conversation_repo.get_by_id(db_session, body.conversation_id)
    if not conversation:
        raise conversation_error.ConversationNotFoundError  # 对话不存在
    await conversation_repo.modify(db_session, conversation, body.title)


@router.post("/delete")
async def api_delete_conversations(
    body: conversation_schema.DeleteConversationRequest,
    db_session: Annotated[AsyncSession, Depends(db.get_app_db)],
) -> None:
    """批量删除对话"""
    logger.info(f"User delete conversations: conversation_ids={body.conversation_ids}")
    await conversation_repo.remove(db_session, body.conversation_ids)
