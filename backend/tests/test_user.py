from faker import Faker

fake = Faker("zh_CN")


def generate_test_email():
    """生成以 test_ 开头的测试用户邮箱"""
    return f"test_{fake.email()}"


def test_register_success(client):
    """测试成功注册"""
    email = generate_test_email()
    username = fake.user_name()
    password = fake.password()

    response = client.post(
        "/api/v1/user/register",
        json={
            "email": email,
            "username": username,
            "password": password,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_register_email_exists(client):
    """测试注册时邮箱已存在"""
    # 先注册一个用户
    email = generate_test_email()
    username = fake.user_name()
    password = fake.password()

    client.post(
        "/api/v1/user/register",
        json={
            "email": email,
            "username": username,
            "password": password,
        },
    )

    # 尝试用相同邮箱再次注册
    response = client.post(
        "/api/v1/user/register",
        json={
            "email": email,
            "username": username,
            "password": password,
        },
    )
    assert response.status_code == 409
    assert "邮箱" in response.json()["detail"]


def test_register_invalid_email(client):
    """测试注册时邮箱格式无效"""
    username = fake.user_name()
    password = fake.password()

    response = client.post(
        "/api/v1/user/register",
        json={
            "email": "invalid-email",
            "username": username,
            "password": password,
        },
    )
    assert response.status_code == 422


def test_register_short_password(client):
    """测试注册时密码过短"""
    email = generate_test_email()
    username = fake.user_name()

    response = client.post(
        "/api/v1/user/register",
        json={
            "email": email,
            "username": username,
            "password": "123",
        },
    )
    assert response.status_code == 422


def test_login_success(client):
    """测试成功登录"""
    email = generate_test_email()
    username = fake.user_name()
    password = fake.password()

    # 先注册用户
    client.post(
        "/api/v1/user/register",
        json={
            "email": email,
            "username": username,
            "password": password,
        },
    )

    # 登录
    response = client.post(
        "/api/v1/user/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_email(client):
    """测试登录时邮箱不存在"""
    email = generate_test_email()
    password = fake.password()

    response = client.post(
        "/api/v1/user/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 401
    assert "用户不存在" in response.json()["detail"]


def test_login_invalid_password(client):
    """测试登录时密码错误"""
    email = generate_test_email()
    username = fake.user_name()
    password = fake.password()

    # 先注册用户
    client.post(
        "/api/v1/user/register",
        json={
            "email": email,
            "username": username,
            "password": password,
        },
    )

    # 用错误密码登录
    response = client.post(
        "/api/v1/user/login",
        json={"email": email, "password": password + "1"},
    )
    assert response.status_code == 401
    assert "密码错误" in response.json()["detail"]


def test_get_me_success(client):
    """测试获取当前用户信息"""
    email = generate_test_email()
    username = fake.user_name()
    password = fake.password()

    # 注册并登录
    register_response = client.post(
        "/api/v1/user/register",
        json={
            "email": email,
            "username": username,
            "password": password,
        },
    )
    token = register_response.json()["access_token"]

    # 获取用户信息
    response = client.get(
        "/api/v1/user/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert data["username"] == username
    assert "groups" in data
    assert "normal" in data["groups"]


def test_get_me_no_token(client):
    """测试获取用户信息时未提供token"""
    response = client.get("/api/v1/user/me")
    assert response.status_code == 401


def test_get_me_invalid_token(client):
    """测试获取用户信息时token无效"""
    response = client.get(
        "/api/v1/user/me", headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401


def test_update_username_success(client):
    """测试成功修改用户名"""
    email = generate_test_email()
    username = fake.user_name()
    password = fake.password()
    new_username = fake.user_name()

    # 注册并登录
    register_response = client.post(
        "/api/v1/user/register",
        json={
            "email": email,
            "username": username,
            "password": password,
        },
    )
    token = register_response.json()["access_token"]

    # 修改用户名
    response = client.post(
        "/api/v1/user/me/username",
        json={"username": new_username},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 202


def test_update_username_same(client):
    """测试修改用户名为相同值"""
    email = generate_test_email()
    username = fake.user_name()
    password = fake.password()

    # 注册并登录
    register_response = client.post(
        "/api/v1/user/register",
        json={
            "email": email,
            "username": username,
            "password": password,
        },
    )
    token = register_response.json()["access_token"]

    # 尝试修改为相同用户名
    response = client.post(
        "/api/v1/user/me/username",
        json={"username": username},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert "用户名相同" in response.json()["detail"]


def test_update_username_no_token(client):
    """测试修改用户名时未提供token"""
    response = client.post(
        "/api/v1/user/me/username", json={"username": fake.user_name()}
    )
    assert response.status_code == 401


def test_update_email_success(client):
    """测试成功修改邮箱"""
    email = generate_test_email()
    username = fake.user_name()
    password = fake.password()
    new_email = generate_test_email()

    # 注册并登录
    register_response = client.post(
        "/api/v1/user/register",
        json={
            "email": email,
            "username": username,
            "password": password,
        },
    )
    token = register_response.json()["access_token"]

    # 修改邮箱
    response = client.post(
        "/api/v1/user/me/email",
        json={"email": new_email},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 202


def test_update_email_same(client):
    """测试修改邮箱为相同值"""
    email = generate_test_email()
    username = fake.user_name()
    password = fake.password()

    # 注册并登录
    register_response = client.post(
        "/api/v1/user/register",
        json={
            "email": email,
            "username": username,
            "password": password,
        },
    )
    token = register_response.json()["access_token"]

    # 尝试修改为相同邮箱
    response = client.post(
        "/api/v1/user/me/email",
        json={"email": email},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400
    assert "邮箱相同" in response.json()["detail"]


def test_update_password_success(client):
    """测试成功修改密码"""
    email = generate_test_email()
    username = fake.user_name()
    password = fake.password()
    new_password = fake.password()

    # 注册并登录
    register_response = client.post(
        "/api/v1/user/register",
        json={
            "email": email,
            "username": username,
            "password": password,
        },
    )
    refresh_token = register_response.json()["refresh_token"]

    # 修改密码（使用 Cookie）
    client.cookies.set("refresh_token", refresh_token)
    response = client.post(
        "/api/v1/user/me/password",
        json={"password": new_password},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_update_password_same(client):
    """测试修改密码为相同值"""
    email = generate_test_email()
    username = fake.user_name()
    password = fake.password()

    # 注册并登录
    register_response = client.post(
        "/api/v1/user/register",
        json={
            "email": email,
            "username": username,
            "password": password,
        },
    )
    refresh_token = register_response.json()["refresh_token"]

    # 尝试修改为相同密码（使用 Cookie）
    client.cookies.set("refresh_token", refresh_token)
    response = client.post(
        "/api/v1/user/me/password",
        json={"password": password},
    )
    assert response.status_code == 400
    assert "密码相同" in response.json()["detail"]


def test_logout_success(client):
    """测试成功登出"""
    email = generate_test_email()
    username = fake.user_name()
    password = fake.password()

    # 注册并登录
    register_response = client.post(
        "/api/v1/user/register",
        json={
            "email": email,
            "username": username,
            "password": password,
        },
    )
    refresh_token = register_response.json()["refresh_token"]

    # 登出（使用 Cookie）
    client.cookies.set("refresh_token", refresh_token)
    response = client.post("/api/v1/user/logout")
    assert response.status_code == 200


def test_refresh_token_success(client):
    """测试成功刷新令牌"""
    email = generate_test_email()
    username = fake.user_name()
    password = fake.password()

    # 注册并登录
    register_response = client.post(
        "/api/v1/user/register",
        json={
            "email": email,
            "username": username,
            "password": password,
        },
    )
    refresh_token_val = register_response.json()["refresh_token"]

    # 使用 refresh_token 获取新令牌（使用 Cookie）
    client.cookies.set("refresh_token", refresh_token_val)
    response = client.post("/api/v1/user/refresh")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_refresh_token_no_token(client):
    """测试刷新令牌时未提供token"""
    response = client.post("/api/v1/user/refresh")
    assert response.status_code == 401


def test_refresh_token_invalid_token(client):
    """测试刷新令牌时使用无效token"""
    client.cookies.set("refresh_token", "invalid_refresh_token")
    response = client.post("/api/v1/user/refresh")
    assert response.status_code == 401
