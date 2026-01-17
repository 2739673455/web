import httpx
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config.config import CFG
from app.main import app

# 创建测试数据库引擎（使用连接池）
TEST_DATABASE_URL = f"mysql+asyncmy://{CFG.db.auth.user}:{CFG.db.auth.password}@{CFG.db.auth.host}:{CFG.db.auth.port}/{CFG.db.auth.database}"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=5,
    max_overflow=10,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="function")
async def db_session():
    """创建独立的数据库会话"""
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession):
    """创建异步测试客户端，注入测试数据库会话"""

    # 依赖注入覆盖
    def override_get_auth_db():
        yield db_session

    from app.dependencies.database import get_auth_db

    app.dependency_overrides[get_auth_db] = override_get_auth_db

    try:
        async with AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac
    finally:
        # 清理依赖注入覆盖
        app.dependency_overrides.clear()


@pytest.fixture(scope="session", autouse=True)
async def cleanup_test_database():
    """测试会话结束后清理数据库连接"""
    yield
    # 测试会话结束后清理
    await test_engine.dispose()
