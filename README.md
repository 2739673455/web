# 聊天后端系统

## 核心功能
- 用户注册和登录 (JWT 认证)
- 用户自定义模型配置 (OpenAI 兼容 API)
- API 密钥安全存储和传输
- 对话管理 (创建、列表、删除，自动生成标题)
- 实时流式聊天 (WebSocket 支持)
- 消息历史存储

## 技术栈
- **后端框架**: FastAPI (异步支持，自动 API 文档)
- **数据库**: MySQL 8.0+
- **ORM**: SQLAlchemy 2.0+ (异步支持)
- **认证**: JWT (PyJWT)
- **密码哈希**: pwdlib
- **加密**: cryptography (Fernet AES 加密)
- **AI 集成**: OpenAI Python SDK
- **验证**: Pydantic
- **包管理**: uv
- **Python 版本**: 3.12+

## API 设计
### 认证相关
#### POST /auth/register
用户注册
- 请求体:
```json
{
  "username": "用户名",
  "email": "邮箱",
  "password": "密码"
}
```
#### POST /auth/login
用户登录
- 请求体:
```json
{
  "email": "邮箱",
  "password": "密码"
}
```
#### GET /auth/me
获取当前用户信息
- 认证: Bearer Token
#### POST /auth/me/username
修改用户名
- 认证: Bearer Token
- 请求体:
```json
{
  "username": "新用户名"
}
```
#### POST /auth/me/email
修改邮箱
- 认证: Bearer Token
- 请求体:
```json
{
  "email": "新邮箱"
}
```
#### POST /auth/me/password
修改密码
- 认证: Bearer Token
- 请求体:
```json
{
  "password": "新密码"
}
```
#### POST /auth/logout
用户登出（使当前 token 失效）
- 认证: Bearer Token
### 配置管理
#### GET /auth/config
获取用户所有模型配置列表 (不含 API 密钥)
- 认证: Bearer Token
#### POST /auth/config/create
创建新的模型配置
- 认证: Bearer Token
- 请求体:
```json
{
  "model_url": "OpenAI 兼容 API URL",
  "model_name": "模型名称",
  "api_key": "API 密钥"
}
```
#### POST /auth/config/{id}/update
更新指定模型配置
- 认证: Bearer Token
- 路径参数: id (配置 ID)
- 请求体:
```json
{
  "model_url": "OpenAI 兼容 API URL",
  "model_name": "模型名称",
  "api_key": "API 密钥"
}
```
### 对话管理
#### GET /conversations
获取用户对话列表
- 认证: Bearer Token
- 查询参数:
  - limit: int (默认 20, 最大 100)
  - offset: int (默认 0)
#### POST /conversations/create
创建新对话
- 认证: Bearer Token
- 请求体: 可选
```json
{
  "title": "对话标题"
}
```
#### POST /conversations/{id}/delete
删除对话
- 认证: Bearer Token
- 路径参数: id (对话 ID)
### 聊天功能
#### GET /conversations/{id}
获取对话消息历史
- 认证: Bearer Token
- 路径参数: id (对话 ID)
- 查询参数:
  - limit: int (默认 50, 最大 200)
  - before_id: int (分页用)
#### POST /conversations/{id}/chat
发送消息并获取 AI 回复
- 认证: Bearer Token
- 路径参数: id (对话 ID)
- 请求体:
```json
{
  "content": "用户消息内容"
}
```

## 安全设计
### API 密钥管理
- **加密存储**: 使用 Fernet 对称加密
- **传输安全**: HTTPS + JWT 认证
- **使用策略**: 临时解密，仅在 API 调用时
### 认证安全
- **JWT 配置**:
  - 算法: HS256
  - access_token 过期时间: 1小时
  - refresh_token 过期时间: 7天
  - 双 token 机制: access_token 用于访问资源，refresh_token 用于刷新 access_token
- **密码策略**: pwdlib (Argon2) 哈希，盐值自动生成
- **会话管理**: refresh_token 存储在数据库，登出时失效
### 其他安全措施
- **CORS**: 配置允许的前端域名
- **HTTPS 强制**: 生产环境必须启用

## 依赖注入与中间件

本项目使用 FastAPI 的依赖注入系统处理认证和业务逻辑，使用中间件处理全局性的 HTTP 请求/响应需求。

### 依赖注入 (Dependency Injection)

#### 已实现的依赖

| 依赖名称 | 文件位置 | 功能描述 |
|---------|---------|---------|
| `oauth2_scheme` | `app/dependencies/auth.py:20` | HTTPBearer 认证方案，用于解析 Bearer Token |
| `authentication()` | `app/dependencies/auth.py:236-280` | JWT 访问令牌验证依赖函数 |
| `get_current_user()` | `app/dependencies/user.py:12-31` | 获取当前登录用户信息 |
| `get_auth_db` | `app/dependencies/database.py:59` | 认证数据库会话提供者 |
| `get_app_db` | `app/dependencies/database.py:58` | 应用数据库会话提供者 |

#### 待实现的依赖

| 依赖名称 | 功能描述 | 关联端点 |
|---------|---------|---------|
| `get_user_configs()` | 获取用户模型配置列表 | `GET /auth/config` |
| `create_user_config()` | 创建新的模型配置 | `POST /auth/config/create` |
| `update_user_config()` | 更新指定模型配置 | `POST /auth/config/{id}/update` |
| `get_user_conversations()` | 获取用户对话列表 | `GET /conversations` |
| `create_conversation()` | 创建新对话 | `POST /conversations/create` |
| `delete_conversation()` | 删除对话 | `POST /conversations/{id}/delete` |
| `get_conversation_messages()` | 获取对话消息历史 | `GET /conversations/{id}` |
| `send_message()` | 发送消息并获取 AI 回复 | `POST /conversations/{id}/messages` |
| `websocket_auth()` | WebSocket 连接认证 | `WebSocket /conversations/ws/{id}` |
| `ai_service()` | AI 服务集成依赖 | 聊天相关端点 |
| `encryption_service()` | API 密钥加密/解密服务 | 配置管理端点 |

#### 依赖注入使用示例

```python
from fastapi import Depends, APIRouter
from app.dependencies.user import get_current_user
from app.dependencies.database import get_app_db

router = APIRouter()

@router.get("/protected-endpoint")
async def protected_endpoint(
    current_user = Depends(get_current_user),
    session = Depends(get_app_db)
):
    # 当前用户和数据库会话已自动注入
    return {"user_id": current_user.id}
```

### 中间件 (Middleware)

#### 已实现的中间件功能

- **密码哈希**: 使用 pwdlib (Argon2) 在 `app/dependencies/auth.py`
- **日志记录**: 部分日志功能在 `app/utils/log.py`

#### 待实现的中间件

| 中间件名称 | 功能描述 | 实现位置 |
|-----------|---------|---------|
| **CORS 中间件** | 配置允许的前端域名，防止跨域攻击 | `app/main.py` |
| **HTTPS 强制中间件** | 生产环境强制使用 HTTPS，确保传输安全 | `app/main.py` |
| **请求日志中间件** | 记录所有请求的来源 IP、时间、路径等信息 | `app/main.py` |
| **限流中间件** | 防止暴力破解和 API 滥用 | `app/main.py` |

#### 中间件实现示例

```python
# CORS 中间件示例
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTPS 强制中间件示例
@app.middleware("http")
async def https_enforce_middleware(request: Request, call_next):
    if not request.url.hostname == "localhost" and request.url.scheme == "http":
        raise HTTPException(status_code=403, detail="HTTPS is required")
    return await call_next(request)

# 请求日志中间件示例
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.2f}s")
    return response
```

### 依赖注入与中间件的关系

```
客户端请求
    │
    ▼
┌─────────────────────────────────────┐
│ 中间件层 (Middleware)                │
│  - CORS 配置                        │
│  - HTTPS 强制                       │
│  - 请求日志                         │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 路由层 (Router)                     │
│  - 使用 Depends() 声明依赖           │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 依赖层 (Dependencies)               │
│  - authentication() 验证 JWT         │
│  - get_current_user() 获取用户       │
│  - get_auth_db / get_app_db 会话     │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 服务层 (Services)                   │
│  - AI 服务调用                      │
│  - 对话管理                         │
│  - 加密/解密操作                    │
└─────────────────────────────────────┘
```

## 项目结构
```bash
web/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置管理
│   ├── database.py             # 数据库连接
│   ├── encryption.py           # 加密工具
│   ├── entities/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── config.py
│   │   ├── conversation.py
│   │   └── message.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── config.py
│   │   ├── conversation.py
│   │   └── message.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── config.py
│   │   ├── conversations.py
│   │   └── chat.py
│   ├── dependencies/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── database.py
│   │   └── user.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_service.py
│   │   └── conversation_service.py
│   └── utils/
│       ├── __init__.py
│       ├── security.py
│       └── websocket.py
├── pyproject.toml
├── README.md
└── Dockerfile
```