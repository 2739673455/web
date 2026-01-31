from conftest import (
    create_conversation,
    create_model_config,
    get_token,
)


def test_get_conversations_empty(client):
    """测试获取空对话列表"""
    token = get_token(client)

    response = client.get(
        "/api/v1/conversation", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["conversations"] == []


def test_create_conversation_multiple(client):
    """测试创建多个对话"""
    token = get_token(client)
    model_config_id = create_model_config(client, token)

    # 创建多个对话
    conversation_ids = []
    for _ in range(3):
        conversation_id = create_conversation(client, token, model_config_id)
        conversation_ids.append(conversation_id)

    # 验证对话列表
    response = client.get(
        "/api/v1/conversation", headers={"Authorization": f"Bearer {token}"}
    )
    data = response.json()
    assert len(data["conversations"]) == 3


def test_delete_conversations_success(client):
    """测试成功批量删除对话"""
    token = get_token(client)
    model_config_id = create_model_config(client, token)

    # 创建多个对话
    conversation_ids = []
    for _ in range(3):
        conversation_id = create_conversation(client, token, model_config_id)
        conversation_ids.append(conversation_id)

    # 批量删除
    response = client.post(
        "/api/v1/conversation/delete",
        json={"ids": conversation_ids},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204

    # 验证已删除
    get_response = client.get(
        "/api/v1/conversation", headers={"Authorization": f"Bearer {token}"}
    )
    data = get_response.json()
    assert data["conversations"] == []


def test_delete_conversations_not_found(client):
    """测试批量删除不存在的对话"""
    token = get_token(client)

    response = client.post(
        "/api/v1/conversation/delete",
        json={"ids": [99999]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert "不存在" in response.json()["detail"]


def test_conversation_crud_full_flow(client):
    """测试对话的完整CRUD流程"""
    token = get_token(client)

    # 1. 创建模型配置
    model_config_id = create_model_config(
        client,
        token,
        name="CRUD Test Config",
        base_url="https://api.test.com/v1",
        model_name="test-model",
        api_key="sk-test",
    )

    # 2. 创建对话
    create_response = client.post(
        "/api/v1/conversation/create",
        json={"model_config_id": model_config_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_response.status_code == 201
    conversation_id = create_response.json()["conversation_id"]

    # 3. 读取对话列表
    list_response = client.get(
        "/api/v1/conversation", headers={"Authorization": f"Bearer {token}"}
    )
    assert list_response.status_code == 200
    assert len(list_response.json()["conversations"]) == 1

    # 4. 删除对话
    delete_response = client.post(
        "/api/v1/conversation/delete",
        json={"ids": [conversation_id]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_response.status_code == 204

    # 5. 验证删除
    final_response = client.get(
        "/api/v1/conversation", headers={"Authorization": f"Bearer {token}"}
    )
    assert final_response.json()["conversations"] == []
