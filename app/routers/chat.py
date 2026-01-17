from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from app.schemas.message import (
    SendMessageRequest,
    MessageListResponse,
)
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/conversations", tags=["聊天功能"])


@router.get("/{id}", response_model=MessageListResponse)
async def get_conversation_messages(id: int, limit: int = 50, before_id: int | None = None):
    """获取对话消息历史"""
    # TODO: 实现获取消息历史逻辑
    return MessageListResponse(
        messages=[
            {
                "id": 1,
                "sender": "user",
                "content": "你好",
                "timestamp": "2024-01-01T00:00:00Z"
            },
            {
                "id": 2,
                "sender": "ai",
                "content": "你好！有什么可以帮助您的吗？",
                "timestamp": "2024-01-01T00:00:01Z"
            }
        ],
        has_more=False
    )


@router.post("/{id}/messages")
async def send_message(id: int, request: SendMessageRequest):
    """发送消息并获取 AI 回复"""
    # TODO: 实现发送消息逻辑，流式回复通过 WebSocket
    return MessageResponse(message="消息已发送")


@router.websocket("/ws/conversations/{id}")
async def websocket_chat(websocket: WebSocket, id: int, token: str = Query(...)):
    """实时流式聊天"""
    await websocket.accept()
    try:
        # TODO: 验证 token
        while True:
            data = await websocket.receive_json()
            # TODO: 处理消息并流式返回 AI 回复
            await websocket.send_json({
                "type": "chunk",
                "content": "AI回复片段"
            })
    except WebSocketDisconnect:
        pass