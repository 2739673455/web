from typing import Annotated

from app.schemas.chat import (
    ConversationTitleResponse,
    MessageItem,
    MessageListResponse,
    SendMessageRequest,
)
from app.services.chat import (
    generate_title,
    get_messages,
    image_url_to_get_presigned_url,
    stream_response,
)
from app.utils import db
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/chat", tags=["聊天"])


@router.post("/generate_title", response_model=ConversationTitleResponse)
async def api_generate_conversation_title(
    body: SendMessageRequest,
) -> ConversationTitleResponse:
    """生成对话标题"""
    logger.info(f"User generate conversation title: {body.conversation_id}")
    # 转换预签名上传url为预签名下载url
    await image_url_to_get_presigned_url(body.messages)
    # 生成标题
    title = await generate_title(
        body.messages[0].content,
        body.base_url,
        body.model_name,
        body.api_key,
    )
    return ConversationTitleResponse(title=title)


@router.post("/send")
async def api_send_message(
    request: Request,
    body: SendMessageRequest,
    db_session: Annotated[AsyncSession, Depends(db.get_app_db)],
):
    """发送消息,获取AI流式回复"""
    payload = request.state.payload
    logger.info(f"User send message: conversation_id={body.conversation_id}")
    return StreamingResponse(
        stream_response(
            conversation_id=body.conversation_id,
            user_id=payload.sub,
            messages=body.messages,
            base_url=body.base_url,
            model_name=body.model_name,
            api_key=body.api_key,
            params=body.params,
            db_session=db_session,
        ),
        media_type="text/plain",
    )
