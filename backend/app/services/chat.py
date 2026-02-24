import json

from app.entities.chat import Message
from app.utils.call_model import call_model, stream_model
from loguru import logger
from openai import (
    APIError as OpenAIError,
)
from openai import (
    AuthenticationError as OpenAIAuthenticationError,
)
from openai import (
    BadRequestError as OpenAIBadRequestError,
)
from openai import (
    InternalServerError as OpenAIInternalError,
)
from openai import (
    NotFoundError as OpenAINotFoundError,
)
from openai import (
    RateLimitError as OpenAIRateLimitError,
)
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.schemas.message import MessageItem


async def _save_message_in_db(
    db_session: AsyncSession,
    last_message: MessageItem,
    user_id: int,
    conversation_id: int,
) -> Message:
    """保存消息到数据库"""
    message = Message(
        user_id=user_id,
        conversation_id=conversation_id,
        role=last_message.role,
        content=json.dumps(
            last_message.content, ensure_ascii=False
        ),  # 将str或list[dict]转换为json字符串
    )
    db_session.add(message)
    try:
        await db_session.commit()
        await db_session.refresh(message)
    except Exception:
        await db_session.rollback()
        raise
    return message


async def stream_response(
    conversation_id: int,
    user_id: int,
    messages: list[MessageItem],
    model_code: str,
    db_session: AsyncSession,
):
    """流式返回AI回复"""
    try:
        # 用户消息存入数据库
        user_message_id = messages[-1].message_id
        if not user_message_id:  # 如果没有消息id才存入数据库
            user_message = await _save_message_in_db(
                db_session, messages[-1], user_id, conversation_id
            )
            user_message_id = user_message.id

        # 返回用户消息id
        yield (
            json.dumps({"type": "user_message_id", "user_message_id": user_message_id})
            + "\n"
        )

        # 流式调用模型
        chunks: list[str] = []
        async for chunk in stream_model(
            messages, base_url, model_name, api_key, params
        ):
            chunks.append(chunk)
            yield (
                json.dumps({"type": "ai_chunk", "content": chunk}, ensure_ascii=False)
                + "\n"
            )

        # AI回复存入数据库
        ai_message = await _save_message_in_db(
            db_session,
            MessageItem(role="assistant", content="".join(chunks)),
            user_id,
            conversation_id,
        )

        # 发送完成信号，返回AI消息id
        yield (json.dumps({"type": "complete", "ai_message_id": ai_message.id}) + "\n")

    except (
        OpenAINotFoundError,
        OpenAIBadRequestError,
        OpenAIAuthenticationError,
        OpenAIRateLimitError,
        OpenAIInternalError,
        OpenAIError,
    ) as e:
        logger.error(f"OpenAI API error: {e}")
        yield json.dumps({"type": "error", "detail": str(e)}, ensure_ascii=False) + "\n"
    except Exception as e:
        logger.error(f"Unexpected error in stream_response: {e}")
        yield json.dumps({"type": "error", "detail": str(e)}, ensure_ascii=False) + "\n"


async def generate_title(content: str | list[dict], model_code: str):
    """生成对话标题"""
    return await call_model(
        [
            {
                "role": "system",
                "content": "你需要为下面的用户提问生成一句简短的概括性标题，字数尽量在20字以内，不要带有句号",
            },
            {"role": "user", "content": content},
        ],
        base_url,
        model_name,
        api_key,
        None,
    )
