import sys
from pathlib import Path

# 将项目根目录添加到 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from app.config import CFG
from app.main import app
from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

fake = Faker("zh_CN")


@pytest.fixture(scope="session")
def client():
    """Synchronous test client for FastAPI."""
    with TestClient(app) as tc:
        yield tc


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_users():
    """在测试会话结束后清理测试用户数据"""
    yield
    # 获取测试用户的 ID
    auth_db_url = f"mysql+pymysql://{CFG.db.auth.user}:{CFG.db.auth.password}@{CFG.db.auth.host}:{CFG.db.auth.port}/{CFG.db.auth.database}"
    auth_engine = create_engine(auth_db_url)
    with auth_engine.connect() as conn:
        result = conn.execute(text("SELECT id FROM user WHERE email LIKE 'test_%'"))
        user_ids = [row[0] for row in result.fetchall()]

        if user_ids:
            placeholders = ", ".join([f":id_{i}" for i in range(len(user_ids))])
            params = {f"id_{i}": uid for i, uid in enumerate(user_ids)}

            conn.execute(
                text(f"DELETE FROM group_user_rel WHERE user_id IN ({placeholders})"),
                params,
            )
            conn.execute(
                text(f"DELETE FROM refresh_token WHERE user_id IN ({placeholders})"),
                params,
            )
            conn.execute(text("DELETE FROM user WHERE email LIKE 'test_%'"))
            conn.commit()
    auth_engine.dispose()

    # 清理 app 库
    if user_ids:
        app_db_url = f"mysql+pymysql://{CFG.db.app.user}:{CFG.db.app.password}@{CFG.db.app.host}:{CFG.db.app.port}/{CFG.db.app.database}"
        app_engine = create_engine(app_db_url)
        with app_engine.connect() as conn:
            placeholders = ", ".join([f":id_{i}" for i in range(len(user_ids))])
            params = {f"id_{i}": uid for i, uid in enumerate(user_ids)}

            conn.execute(
                text(
                    f"DELETE FROM message WHERE conversation_id IN (SELECT id FROM conversation WHERE user_id IN ({placeholders}))"
                ),
                params,
            )
            conn.execute(
                text(f"DELETE FROM conversation WHERE user_id IN ({placeholders})"),
                params,
            )
            conn.execute(
                text(f"DELETE FROM model_config WHERE user_id IN ({placeholders})"),
                params,
            )
            conn.commit()
        app_engine.dispose()


def get_token(client):
    """辅助函数：注册用户并返回 access_token"""
    register_response = client.post(
        "/api/v1/user/register",
        json={
            "email": f"test_{fake.email()}",
            "username": fake.user_name(),
            "password": fake.password(),
        },
    )
    return register_response.json()["access_token"]


def create_model_config(
    client, token, name=None, base_url=None, model_name=None, api_key=None
):
    """辅助函数：创建模型配置并返回配置ID"""
    response = client.post(
        "/api/v1/model_config/create",
        json={
            "name": name or fake.word(),
            "base_url": base_url or fake.url(),
            "model_name": model_name or fake.word(),
            "api_key": api_key or fake.password(),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    return response.json()["config_id"]


def create_conversation(client, token, model_config_id):
    """辅助函数：创建对话并返回对话ID"""
    response = client.post(
        "/api/v1/conversation/create",
        json={"model_config_id": model_config_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    return response.json()["conversation_id"]
