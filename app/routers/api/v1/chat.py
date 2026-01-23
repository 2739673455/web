import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import authenticate_access_token
from app.dependencies.database import get_app_db
from app.schemas.chat import (
    GetUploadPresignedUrlRequest,
    GetUploadPresignedUrlResponse,
    MessageItem,
    MessageListResponse,
    SendMessageRequest,
)
from app.schemas.user import AccessTokenPayload
from app.services.chat import (
    get_messages,
    image_url_to_cos_url,
    image_url_to_get_presigned_url,
    save_message_in_db,
)
from app.utils.call_model import stream_model
from app.utils.cos import generate_image_cos_key, get_upload_presigned_url

router = APIRouter(prefix="/chat", tags=["聊天功能"])


@router.post("/get_upload_presigned_url", response_model=GetUploadPresignedUrlResponse)
async def api_get_upload_presigned_url(
    request: GetUploadPresignedUrlRequest,
    payload: Annotated[AccessTokenPayload, Depends(authenticate_access_token)],
):
    """获取带预签名的上传url"""
    cos_keys = [
        generate_image_cos_key(payload.sub, request.conversation_id, suffix)
        for suffix in request.suffixes
    ]  # 生成cos_key
    upload_presigned_urls = await asyncio.gather(
        *[get_upload_presigned_url(key) for key in cos_keys]
    )  # 获取预签名上传url
    return GetUploadPresignedUrlResponse(urls=upload_presigned_urls)


@router.get("/{conversation_id}", response_model=MessageListResponse)
async def api_get_messages(
    conversation_id: int,
    session: Annotated[AsyncSession, Depends(get_app_db)],
    payload: Annotated[AccessTokenPayload, Depends(authenticate_access_token)],
):
    """获取消息记录"""
    messages = await get_messages(session, conversation_id)
    # 转换cos_url为预签名下载url
    await image_url_to_get_presigned_url(messages)
    return MessageListResponse(
        messages=[
            MessageItem(
                message_id=message.id,
                role=message.role,
                content=message.content,
                timestamp=message.timestamp,
            )
            for message in messages
        ]
    )


@router.post("/send")
async def api_send_message(
    request: SendMessageRequest,
    session: Annotated[AsyncSession, Depends(get_app_db)],
    payload: Annotated[AccessTokenPayload, Depends(authenticate_access_token)],
):
    """发送消息,获取AI流式回复"""
    # 转换图片url为cos_url
    await image_url_to_cos_url(request.messages)
    # 用户消息存入数据库
    user_message = await save_message_in_db(
        session, request.messages[-1], payload.sub, request.conversation_id
    )
    # 转换cos_url为预签名下载url
    await image_url_to_get_presigned_url(request.messages)

    async def generate_response():
        chunks: list[str] = []
        async for chunk in stream_model(
            request.messages,
            request.base_url,
            request.model_name,
            request.encrypted_api_key,
            request.params,
        ):
            chunks.append(chunk)
            yield chunk
        # AI回复存入数据库
        ai_message = await save_message_in_db(
            session,
            MessageItem(role="assistant", content="".join(chunks)),
            payload.sub,
            request.conversation_id,
        )
        # 最后发送消息ID
        yield f'\n\n[END]{{"user_message_id":{user_message.id},"ai_message_id":{ai_message.id}}}'

    return StreamingResponse(
        generate_response(),
        media_type="text/plain",
    )
