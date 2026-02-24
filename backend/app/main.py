from contextlib import asynccontextmanager

import uvicorn
from app.exceptions.handlers import register_exception_handlers
from app.init_db import prepare
from app.middlewares import trace
from app.routers import api
from app.utils import db
from app.utils.log import setup_logger
from fastapi import FastAPI
from loguru import logger


async def init_database_if_needed():
    """如果数据库不存在则自动初始化"""
    db_init, db_sql_orm = prepare()

    # 检查每个数据库是否存在，不存在则初始化
    need_init = []
    for db_name, sql_file_path, output_path in db_sql_orm:
        exists = await db_init.check_db_exists(db_name)
        if not exists:
            need_init.append((db_name, sql_file_path, output_path))
            logger.info(f"数据库 {db_name} 不存在，初始化数据库")
        else:
            logger.info(f"数据库 {db_name} 已存在，跳过初始化")

    if need_init:
        await db_init.init_db(need_init)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger()
    yield
    await db.close_all()


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
