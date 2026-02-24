from fastapi import APIRouter

from . import conversation, message

router = APIRouter(prefix="/api")
router.include_router(conversation.router)
router.include_router(message.router)
