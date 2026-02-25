from typing import Annotated

from app.exceptions import conversation as conversation_error
from app.repositories import conversation as conversation_repo
from app.repositories import message as message_repo
from app.schemas import message as message_schema
from app.services import chat as chat_service
from app.utils import db
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/message", tags=["消息管理"])


@router.get("/{conversation_id}")
async def api_get_conversation(
    conversation_id: int,
    db_session: Annotated[AsyncSession, Depends(db.get_app_db)],
) -> message_schema.MessageListResponse:
    """获取对话消息"""
    logger.info(f"User get messages: {conversation_id=}")
    messages = await message_repo.get_by_conversation_id(db_session, conversation_id)
    return message_schema.MessageListResponse(
        messages=[
            message_schema.MessageItem(
                message_id=message.id,
                role=message.role,
                content=message.content,
                create_at=message.create_at,
            )
            for message in messages
        ]
    )


@router.post("/generate_title")
async def api_generate_title(
    body: message_schema.SendMessageRequest,
) -> message_schema.ConversationTitleResponse:
    """生成对话标题"""
    logger.info(f"User generate conversation title: {body.conversation_id}")
    # 生成标题
    title = await chat_service.generate_title(body.messages[0].content, body.model_code)
    return message_schema.ConversationTitleResponse(title=title)


@router.post("/send")
async def api_send_message(
    request: Request,
    body: message_schema.SendMessageRequest,
    db_session: Annotated[AsyncSession, Depends(db.get_app_db)],
) -> StreamingResponse:
    """发送消息,获取AI流式回复"""
    payload = request.state.payload
    logger.info(f"User send message: conversation_id={body.conversation_id}")

    # 检查对话是否属于该用户
    conversations = await conversation_repo.get_by_user_id(db_session, payload.sub)
    if body.conversation_id not in [i.id for i in conversations]:
        raise conversation_error.ConversationNotFoundError  # 对话不存在

    return StreamingResponse(
        chat_service.stream_response(
            conversation_id=body.conversation_id,
            messages=body.messages,
            model_code=body.model_code,
            db_session=db_session,
        ),
        media_type="text/plain",
    )
