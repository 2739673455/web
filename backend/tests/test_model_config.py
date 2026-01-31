from faker import Faker

fake = Faker()


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


def create_model_config(client, token, name, base_url, model_name, api_key):
    """辅助函数：创建模型配置并返回配置ID"""
    response = client.post(
        "/api/v1/model_config/create",
        json={
            "name": name,
            "base_url": base_url,
            "model_name": model_name,
            "api_key": api_key,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    return response.json()["config_id"]


def test_create_model_config_success(client):
    """测试成功创建模型配置"""
    token = get_token(client)

    name = fake.word()
    base_url = fake.url()
    model_name = fake.word()
    api_key = fake.password()

    response = client.post(
        "/api/v1/model_config/create",
        json={
            "name": name,
            "base_url": base_url,
            "model_name": model_name,
            "api_key": api_key,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201


def test_create_model_config_no_token(client):
    """测试创建模型配置时未提供token"""
    response = client.post(
        "/api/v1/model_config/create",
        json={
            "name": fake.name(),
            "base_url": fake.url(),
            "model_name": fake.word(),
            "api_key": fake.password(),
        },
    )
    assert response.status_code == 401


def test_create_model_config_invalid_token(client):
    """测试创建模型配置时token无效"""
    response = client.post(
        "/api/v1/model_config/create",
        json={
            "name": fake.name(),
            "base_url": fake.url(),
            "model_name": fake.word(),
            "api_key": fake.password(),
        },
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401


def test_get_model_configs_empty(client):
    """测试获取空模型配置列表"""
    token = get_token(client)

    response = client.get(
        "/api/v1/model_config", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["configs"] == []


def test_get_model_configs_with_data(client):
    """测试获取模型配置列表（包含数据）"""
    token = get_token(client)

    # 创建配置
    config_id = create_model_config(
        client,
        token,
        name="test_config",
        base_url="https://api.openai.com/v1",
        model_name="gpt-4",
        api_key="sk-test123",
    )

    # 获取列表
    response = client.get(
        "/api/v1/model_config", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["configs"]) == 1
    assert data["configs"][0]["config_id"] == config_id
    assert data["configs"][0]["name"] == "test_config"
    assert data["configs"][0]["base_url"] == "https://api.openai.com/v1"
    assert data["configs"][0]["model_name"] == "gpt-4"
    assert data["configs"][0]["api_key"] == "sk-test123"


def test_get_model_configs_no_token(client):
    """测试获取模型配置列表时未提供token"""
    response = client.get("/api/v1/model_config")
    assert response.status_code == 401


def test_get_model_configs_invalid_token(client):
    """测试获取模型配置列表时token无效"""
    response = client.get(
        "/api/v1/model_config", headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401


def test_update_model_config_success(client):
    """测试成功更新模型配置"""
    token = get_token(client)

    name = fake.name()
    base_url = fake.url()
    model_name = fake.word()
    api_key = fake.password()

    # 创建配置
    config_id = create_model_config(client, token, name, base_url, model_name, api_key)

    # 更新配置
    new_name = fake.name()
    new_base_url = fake.url()
    new_model_name = fake.word()
    new_api_key = fake.password()

    response = client.post(
        "/api/v1/model_config/update",
        json={
            "config_id": config_id,
            "name": new_name,
            "base_url": new_base_url,
            "model_name": new_model_name,
            "api_key": new_api_key,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 202

    # 验证更新
    get_response = client.get(
        "/api/v1/model_config", headers={"Authorization": f"Bearer {token}"}
    )
    data = get_response.json()
    assert data["configs"][0]["name"] == new_name
    assert data["configs"][0]["base_url"] == new_base_url
    assert data["configs"][0]["model_name"] == new_model_name
    assert data["configs"][0]["api_key"] == new_api_key


def test_update_model_config_not_found(client):
    """测试更新不存在的模型配置"""
    token = get_token(client)

    response = client.post(
        "/api/v1/model_config/update",
        json={
            "config_id": 99999,
            "name": fake.name(),
            "base_url": fake.url(),
            "model_name": fake.word(),
            "api_key": fake.password(),
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert "不存在" in response.json()["detail"]


def test_update_model_config_no_token(client):
    """测试更新模型配置时未提供token"""
    response = client.post(
        "/api/v1/model_config/update",
        json={
            "id": 1,
            "name": fake.name(),
            "base_url": fake.url(),
            "model_name": fake.word(),
            "api_key": fake.password(),
        },
    )
    assert response.status_code == 401


def test_update_model_config_invalid_token(client):
    """测试更新模型配置时token无效"""
    response = client.post(
        "/api/v1/model_config/update",
        json={
            "id": 1,
            "name": fake.name(),
            "base_url": fake.url(),
            "model_name": fake.word(),
            "api_key": fake.password(),
        },
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401


def test_delete_model_configs_success(client):
    """测试成功批量删除模型配置"""
    token = get_token(client)

    # 创建多个配置
    config_ids = []
    for i in range(3):
        config_id = create_model_config(
            client,
            token,
            name=f"config_{i}",
            base_url=fake.url(),
            model_name=fake.word(),
            api_key=fake.password(),
        )
        config_ids.append(config_id)

    # 批量删除
    response = client.post(
        "/api/v1/model_config/delete",
        json={"ids": config_ids},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204

    # 验证已删除
    get_response = client.get(
        "/api/v1/model_config", headers={"Authorization": f"Bearer {token}"}
    )
    data = get_response.json()
    assert data["configs"] == []


def test_delete_model_configs_single(client):
    """测试删除单个模型配置（批量接口）"""
    token = get_token(client)

    # 创建配置
    config_id = create_model_config(
        client,
        token,
        name="single_config",
        base_url=fake.url(),
        model_name=fake.word(),
        api_key=fake.password(),
    )

    # 删除单个配置
    response = client.post(
        "/api/v1/model_config/delete",
        json={"ids": [config_id]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204


def test_delete_model_configs_not_found(client):
    """测试批量删除不存在的模型配置"""
    token = get_token(client)

    response = client.post(
        "/api/v1/model_config/delete",
        json={"ids": [99999]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert "不存在" in response.json()["detail"]


def test_delete_model_configs_no_token(client):
    """测试批量删除模型配置时未提供token"""
    response = client.post(
        "/api/v1/model_config/delete",
        json={"ids": [1]},
    )
    assert response.status_code == 401


def test_delete_model_configs_invalid_token(client):
    """测试批量删除模型配置时token无效"""
    response = client.post(
        "/api/v1/model_config/delete",
        json={"ids": [1]},
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401


def test_model_config_crud_full_flow(client):
    """测试模型配置的完整CRUD流程"""
    token = get_token(client)

    # 1. 创建
    name = "CRUD Test Config"
    base_url = "https://api.test.com/v1"
    model_name = "test-model"
    api_key = "sk-test-api-key"

    create_response = client.post(
        "/api/v1/model_config/create",
        json={
            "name": name,
            "base_url": base_url,
            "model_name": model_name,
            "api_key": api_key,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_response.status_code == 201

    # 2. 读取
    list_response = client.get(
        "/api/v1/model_config", headers={"Authorization": f"Bearer {token}"}
    )
    assert list_response.status_code == 200

    config_id = list_response.json()["configs"][0]["config_id"]

    # 3. 更新
    new_name = "Updated Config"
    new_base_url = "https://api.updated.com/v1"
    new_model_name = "updated-model"
    new_api_key = "sk-updated-key"

    update_response = client.post(
        "/api/v1/model_config/update",
        json={
            "config_id": config_id,
            "name": new_name,
            "base_url": new_base_url,
            "model_name": new_model_name,
            "api_key": new_api_key,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update_response.status_code == 202

    # 4. 验证更新
    get_response = client.get(
        "/api/v1/model_config", headers={"Authorization": f"Bearer {token}"}
    )
    config = get_response.json()["configs"][0]
    assert config["name"] == new_name
    assert config["base_url"] == new_base_url
    assert config["model_name"] == new_model_name
    assert config["api_key"] == new_api_key

    # 5. 删除
    delete_response = client.post(
        "/api/v1/model_config/delete",
        json={"ids": [config_id]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_response.status_code == 204

    # 6. 验证删除
    final_response = client.get(
        "/api/v1/model_config", headers={"Authorization": f"Bearer {token}"}
    )
    assert final_response.json()["configs"] == []


def test_can_create_model_config_below_limit(client):
    """测试检查创建权限 - 配置数量低于限制"""
    token = get_token(client)

    response = client.post(
        "/api/v1/model_config/can_create",
        json={"config_count": 2},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["can_create"] is True
    assert data["limit"] == 3


def test_can_create_model_config_at_limit(client):
    """测试检查创建权限 - 配置数量达到限制"""
    token = get_token(client)

    response = client.post(
        "/api/v1/model_config/can_create",
        json={"config_count": 3},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["can_create"] is False
    assert data["limit"] == 3


def test_can_create_model_config_above_limit(client):
    """测试检查创建权限 - 配置数量超过限制"""
    token = get_token(client)

    response = client.post(
        "/api/v1/model_config/can_create",
        json={"config_count": 5},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["can_create"] is False
    assert data["limit"] == 3


def test_can_create_model_config_no_token(client):
    """测试检查创建权限时未提供token"""
    response = client.post(
        "/api/v1/model_config/can_create",
        json={"config_count": 1},
    )
    assert response.status_code == 401


def test_can_create_model_config_invalid_token(client):
    """测试检查创建权限时token无效"""
    response = client.post(
        "/api/v1/model_config/can_create",
        json={"config_count": 1},
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401


def test_can_create_model_config_with_zero_count(client):
    """测试检查创建权限 - 配置数量为0"""
    token = get_token(client)

    response = client.post(
        "/api/v1/model_config/can_create",
        json={"config_count": 0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["can_create"] is True
    assert data["limit"] == 3
