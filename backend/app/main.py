from contextlib import asynccontextmanager

import uvicorn
from app.exceptions.handlers import register_exception_handlers
from app.middlewares import trace
from app.routers import api
from app.services.database import db_manager
from app.utils.log import setup_logger
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger()
    yield
    await db_manager.close_all()


app = FastAPI(lifespan=lifespan)

# 日志中间件
app.middleware("http")(trace.middleware)

# 注册异常处理
register_exception_handlers(app)


@app.get("/health")
async def health():
    return {"status": "healthy"}


app.include_router(api.router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8888)
