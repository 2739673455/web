import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.config import CFG
from app.dependencies.database import db_manager
from app.handlers import register_exception_handlers
from app.middleware import log_middleware
from app.routers.api import api
from app.utils.log import setup_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger()
    yield
    await db_manager.close_all()


app = FastAPI(lifespan=lifespan)

# 日志中间件
app.middleware("http")(log_middleware)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=CFG.cors_origins,  # 允许的来源列表
    allow_credentials=True,  # 允许携带cookie
    allow_methods=["*"],  # 允许的HTTP方法列表
    allow_headers=["*"],  # 允许的请求头列表
)

# 异常处理
register_exception_handlers(app)


@app.get("/health")
async def health():
    return {"status": "healthy"}


app.include_router(api.router)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=CFG.port,
        reload=True,
        reload_dirs=[os.path.dirname(__file__)],
    )
