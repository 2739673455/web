# 启动服务
```bash
docker-compose up -d
```

# 修改 volumes/backend/configs中的配置文件
`config.yml`:
```yaml
db: # 数据库
  app: # 应用数据库
    host: mysql-server <--- 修改
    port: 3306
    user: root
    password: ${oc.env:APP_DB_PASSWORD}
    database: chat
  auth: # 认证数据库
    host: mysql-server <--- 修改
    port: 3306
    user: root
    password: ${oc.env:AUTH_DB_PASSWORD}
    database: auth
...
```

`.env`:
```bash
# 应用数据库密码
APP_DB_PASSWORD=123321
# 认证数据库密码
AUTH_DB_PASSWORD=123321

# 令牌加密密钥 生成: python -c "import secrets; print(secrets.token_hex(32))"
AUTH_SECRET_KEY=d6a5d730ec247d487f17419df966aec9d4c2a09d2efc9699d09757cf94c68b01
# API-Key加密密钥 生成: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=onuuwtwtfgqzvoQsvK5lPWapRw4ny7XGhhQSBIMHptI=

# 腾讯云APPID
COS_APP_ID= <--- 添加
# 腾讯云COS SECRET-ID
COS_SECRET_ID= <--- 添加
# 腾讯云COS SECRET-KEY
COS_SECRET_KEY= <--- 添加
```

# 重启特定服务
```bash
docker-compose restart backend
docker-compose restart frontend
```

# 访问应用
- **前端界面**: http://localhost
- **后端 API DOC**: http://localhost:12321/docs

# 停止服务
```bash
docker-compose down
```

# 重新构建并启动
```bash
docker-compose up -d --build
```