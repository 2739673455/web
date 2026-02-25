import json

from app.config import CFG
from app.repositories import message as message_repo
from app.schemas.message import MessageItem
from app.utils.call_model import call_model, stream_model
from sqlalchemy.ext.asyncio import AsyncSession


async def generate_title(messages: list[MessageItem], model_code: str):
    """调用模型生成对话标题"""
    # 读取模型服务配置
    model = CFG.model_service.models[model_code]

    # 调用模型生成标题
    system_prompt = {
        "role": "system",
        "content": "为下面的内容生成一个对话主题，字数控制在20字以内，不要带句号",
    }
    message_dicts = [i.to_dict() for i in messages]

    return await call_model(
        [system_prompt, *message_dicts],
        model.base_url,
        model.model_name,
        model.api_key,
        None,
    )


async def stream_response(
    conversation_id: int,
    messages: list[MessageItem],
    model_code: str,
    db_session: AsyncSession,
):
    """流式返回AI回复"""
    # 存储用户消息
    last_message = messages[-1]
    if not last_message.message_id:  # 如果用户消息id不存在，则将其存入数据库
        # 转换 message 格式
        message_dict = last_message.to_dict()
        # 将消息存入数据库
        user_message = await message_repo.create(
            db_session,
            conversation_id,
            message_dict["role"],
            json.dumps(message_dict["content"], ensure_ascii=False),
        )
        # 返回用户消息id
        yield (
            json.dumps({"type": "user_message_id", "user_message_id": user_message.id})
            + "\n"
        )

    # 读取模型服务配置
    model = CFG.model_service.models[model_code]

    try:
        # 流式调用模型
        chunks: list[str] = []
        message_dicts = [i.to_dict() for i in messages]
        async for chunk in stream_model(
            message_dicts, model.base_url, model.model_name, model.api_key, model.params
        ):
            # 拼接AI消息
            chunks.append(chunk)

            # 返回AI消息片段
            yield (
                json.dumps({"type": "ai_chunk", "content": chunk}, ensure_ascii=False)
                + "\n"
            )

        # AI消息存入数据库
        ai_message = await message_repo.create(
            db_session, conversation_id, "assistant", "".join(chunks)
        )

        # 发送完成信号，返回AI消息id
        yield (json.dumps({"type": "complete", "ai_message_id": ai_message.id}) + "\n")

    except Exception as e:
        yield json.dumps({"type": "error", "detail": str(e)}, ensure_ascii=False) + "\n"
        raise e
