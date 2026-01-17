from httpx import AsyncClient


async def test_register_success(client: AsyncClient):
    """测试成功注册"""
    response = await client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_register_email_exists(client: AsyncClient):
    """测试注册时邮箱已存在"""
    # 先注册一个用户
    await client.post(
        "/auth/register",
        json={
            "email": "duplicate@example.com",
            "username": "user1",
            "password": "password123",
        },
    )

    # 尝试用相同邮箱再次注册
    response = await client.post(
        "/auth/register",
        json={
            "email": "duplicate@example.com",
            "username": "user2",
            "password": "password123",
        },
    )
    assert response.status_code == 409
    assert "邮箱" in response.json()["detail"]


async def test_register_invalid_email(client: AsyncClient):
    """测试注册时邮箱格式无效"""
    response = await client.post(
        "/auth/register",
        json={
            "email": "invalid-email",
            "username": "testuser",
            "password": "password123",
        },
    )
    assert response.status_code == 422


async def test_register_short_password(client: AsyncClient):
    """测试注册时密码过短"""
    response = await client.post(
        "/auth/register",
        json={"email": "test@example.com", "username": "testuser", "password": "123"},
    )
    assert response.status_code == 422


async def test_register_short_username(client: AsyncClient):
    """测试注册时用户名过短"""
    response = await client.post(
        "/auth/register",
        json={"email": "test@example.com", "username": "ab", "password": "password123"},
    )
    assert response.status_code == 422


async def test_login_success(client: AsyncClient):
    """测试成功登录"""
    # 先注册用户
    await client.post(
        "/auth/register",
        json={
            "email": "login@example.com",
            "username": "loginuser",
            "password": "password123",
        },
    )

    # 登录
    response = await client.post(
        "/auth/login", json={"email": "login@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_login_invalid_email(client: AsyncClient):
    """测试登录时邮箱不存在"""
    response = await client.post(
        "/auth/login",
        json={"email": "nonexistent@example.com", "password": "password123"},
    )
    assert response.status_code == 401
    assert "用户不存在" in response.json()["detail"]


async def test_login_invalid_password(client: AsyncClient):
    """测试登录时密码错误"""
    # 先注册用户
    await client.post(
        "/auth/register",
        json={
            "email": "wrongpass@example.com",
            "username": "user",
            "password": "correctpass",
        },
    )

    # 用错误密码登录
    response = await client.post(
        "/auth/login", json={"email": "wrongpass@example.com", "password": "wrongpass"}
    )
    assert response.status_code == 401
    assert "邮箱或密码错误" in response.json()["detail"]


async def test_get_me_success(client: AsyncClient):
    """测试获取当前用户信息"""
    # 注册并登录
    register_response = await client.post(
        "/auth/register",
        json={
            "email": "me@example.com",
            "username": "meuser",
            "password": "password123",
        },
    )
    token = register_response.json()["access_token"]

    # 获取用户信息
    response = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"
    assert data["username"] == "meuser"
    assert "user_id" in data


async def test_get_me_no_token(client: AsyncClient):
    """测试获取用户信息时未提供token"""
    response = await client.get("/auth/me")
    assert response.status_code == 401


async def test_get_me_invalid_token(client: AsyncClient):
    """测试获取用户信息时token无效"""
    response = await client.get(
        "/auth/me", headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401


async def test_update_username_success(client: AsyncClient):
    """测试成功修改用户名"""
    # 注册并登录
    register_response = await client.post(
        "/auth/register",
        json={
            "email": "updateuser@example.com",
            "username": "oldname",
            "password": "password123",
        },
    )
    token = register_response.json()["access_token"]

    # 修改用户名
    response = await client.post(
        "/auth/me/username",
        json={"username": "newname"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newname"


async def test_update_username_same(client: AsyncClient):
    """测试修改用户名为相同值"""
    # 注册并登录
    register_response = await client.post(
        "/auth/register",
        json={
            "email": "sameuser@example.com",
            "username": "samename",
            "password": "password123",
        },
    )
    token = register_response.json()["access_token"]

    # 尝试修改为相同用户名
    response = await client.post(
        "/auth/me/username",
        json={"username": "samename"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert "用户名相同" in response.json()["detail"]


async def test_update_username_no_token(client: AsyncClient):
    """测试修改用户名时未提供token"""
    response = await client.post("/auth/me/username", json={"username": "newname"})
    assert response.status_code == 401


async def test_update_email_success(client: AsyncClient):
    """测试成功修改邮箱"""
    # 注册并登录
    register_response = await client.post(
        "/auth/register",
        json={
            "email": "oldemail@example.com",
            "username": "emailuser",
            "password": "password123",
        },
    )
    token = register_response.json()["access_token"]

    # 修改邮箱
    response = await client.post(
        "/auth/me/email",
        json={"email": "newemail@example.com"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newemail@example.com"


async def test_update_email_same(client: AsyncClient):
    """测试修改邮箱为相同值"""
    # 注册并登录
    register_response = await client.post(
        "/auth/register",
        json={
            "email": "sameemail@example.com",
            "username": "user",
            "password": "password123",
        },
    )
    token = register_response.json()["access_token"]

    # 尝试修改为相同邮箱
    response = await client.post(
        "/auth/me/email",
        json={"email": "sameemail@example.com"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert "邮箱相同" in response.json()["detail"]


async def test_update_email_no_token(client: AsyncClient):
    """测试修改邮箱时未提供token"""
    response = await client.post(
        "/auth/me/email", json={"email": "newemail@example.com"}
    )
    assert response.status_code == 401


async def test_update_password_success(client: AsyncClient):
    """测试成功修改密码"""
    # 注册并登录
    register_response = await client.post(
        "/auth/register",
        json={
            "email": "pass@example.com",
            "username": "passuser",
            "password": "oldpassword",
        },
    )
    refresh_token = register_response.json()["refresh_token"]

    # 修改密码（使用 Cookie）
    response = await client.post(
        "/auth/me/password",
        json={"password": "newpassword"},
        cookies={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


async def test_update_password_same(client: AsyncClient):
    """测试修改密码为相同值"""
    # 注册并登录
    register_response = await client.post(
        "/auth/register",
        json={
            "email": "samepass@example.com",
            "username": "user",
            "password": "samepassword",
        },
    )
    refresh_token = register_response.json()["refresh_token"]

    # 尝试修改为相同密码（使用 Cookie）
    response = await client.post(
        "/auth/me/password",
        json={"password": "samepassword"},
        cookies={"refresh_token": refresh_token},
    )
    assert response.status_code == 400
    assert "密码相同" in response.json()["detail"]


async def test_logout_success(client: AsyncClient):
    """测试成功登出"""
    # 注册并登录
    register_response = await client.post(
        "/auth/register",
        json={
            "email": "logout@example.com",
            "username": "logoutuser",
            "password": "password123",
        },
    )
    refresh_token = register_response.json()["refresh_token"]

    # 登出（使用 Cookie）
    response = await client.post(
        "/auth/logout", cookies={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
