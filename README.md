# 聊天后端系统
## 功能
### 用户管理 [user](app/routers/api/v1/user.py)
1. 注册 `POST /user/register`
   - 请求体
      - 邮箱
      - 用户名
      - 密码
   1. 数据库中添加用户
   2. 自动登录，返回刷新令牌和访问令牌
2. 登录 `POST /user/login`
   - 请求体
      - 邮箱
      - 密码
   1. 返回刷新令牌和访问令牌
3. 获取个人信息 `GET /user/me`
   - 请求头
      - 访问令牌
   1. 返回用户名、邮箱、密码
4. 修改用户名 `POST /user/me/username`
   - 请求头
      - 访问令牌  
   - 请求体
      - 新用户名
   1. 修改用户名
5. 修改邮箱 `POST /user/me/email`
   - 请求头
      - 访问令牌
   - 请求体
      - 新邮箱
   1. 修改邮箱
6. 修改密码 `POST /user/me/password`
   - 请求头
      - 刷新令牌
   - 请求体
      - 新密码
   1. 修改密码
   2. 撤销刷新令牌
   3. 返回新的刷新令牌和访问令牌
7. 登出 `POST /user/logout`
   - 请求头
      - 刷新令牌
   1. 撤销刷新令牌
### 模型配置管理 [model_config](app/routers/api/v1/model_config.py)
1. 获取模型配置 `GET /model_config`
   - 请求头
     - 访问令牌
   1. 返回用户模型配置列表
2. 检查是否能创建新的模型配置 `POST /model_config/can_create`
   - 请求头
     - 访问令牌
   - 请求体
     - 模型配置数量
   1. 返回能否创建
3. 创建模型配置 `POST /model_config/create`
   - 请求头
     - 访问令牌
   - 请求体
     - 配置名称
     - 模型 url
     - 模型名称
     - 模型 API Key
     - 其他配置参数
   1. 创建模型配置
   2. 返回模型配置信息
4. 更新模型配置 `POST /model_config/update`
   - 请求头
     - 访问令牌
   - 请求体
     - 配置 ID
     - 配置名称
     - 模型 url
     - 模型名称
     - 模型 API Key
     - 其他配置参数
   1. 更新模型配置
5. 批量删除模型配置 `POST /model_config/delete`
   - 请求头
     - 访问令牌
   - 请求体
     - 配置 ID 列表
   1. 删除模型配置
### 对话管理 [conversation](app/routers/api/v1/conversation.py)
1. 获取对话 `GET /conversation`
   - 请求头
     - 访问令牌
   1. 返回用户对话列表
2. 创建对话 `POST /conversation/create`
   - 请求头
     - 访问令牌
   - 请求体
     - 模型配置 ID
   1. 创建对话，返回对话 ID
3. 生成对话标题 `POST /conversation/generate_title`
   - 请求头
     -  访问令牌
   - 请求体
     - 对话 ID
     - 消息 (图片url为预签名上传url)
     - 模型 url
     - 模型名称
     - 模型 API Key
     - 其他配置参数
   1. 处理消息中的预签名上传url为预签名下载url
   2. 调用模型生成标题
   3. 更新数据库中的对话标题
   4. 返回对话标题
4. 删除对话 `POST /conversation/delete`
   - 请求头
     - 访问令牌
   - 请求体
     - 对话 ID 列表
   1. 删除对话
### 聊天功能  [chat](app/routers/api/v1/chat.py)
1. 获取预签名上传url `POST /chat/get_upload_presigned_url`
   - 请求头
     - 访问令牌
   - 请求体
     - 对话 ID
     - 文件后缀名列表
   1. 使用用户ID、对话ID、文件后缀名生成cos_key
   2. 使用cos_key生成预签名上传url，返回相应数量的url
2. 获取消息记录 `GET /chat/{id}`
   - 请求头
     - 访问令牌
   - 请求体
     - 对话 ID
   1. 获取消息记录
   2. 处理消息中的cos_key为预签名下载url
   3. 返回消息记录
3. 发送消息并获取AI流式回复 `POST /chat/send`
   - 请求头
     - 访问令牌
   - 请求体
     - 对话 ID
     - 消息
     - 模型 url
     - 模型名称
     - 模型 API Key
     - 其他配置参数
   1. 处理消息中的图片url为cos_url
   2. 用户消息存入数据库
   3. 处理消息中的cos_url为预签名下载url
   4. 流式返回AI回复
   5. 生成完毕后，AI回复存入数据库
   6. 返回用户消息ID和AI回复消息ID

## 图片存储
腾讯云COS: https://console.cloud.tencent.com/cos  
使用主用户;或者创建子用户并绑定权限 `QcloudCOSFullAccess`  
Python SDK: https://cloud.tencent.com/document/product/436/12269  
使用时需要用到子用户的 `secret_id` 和 `secret_key`，以及主用户的 `APPID`  
图片的key格式为 `user_id/conversation_id/images/xxx.jpg`  
暂时只支持用户发送图片，不支持模型发送图片

## 关键流程
### 创建新模型配置时
1. 用户点击创建新的模型配置
2. 前端请求检查是否能创建新模型配置
3. 后端从访问令牌中获取权限范围，检查是否有权限创建新模型配置
4. 后端返回能否创建新的模型配置
5. 前端根据返回结果创建新模型配置或提醒无权创建新配置
### 新建对话时
1. 用户通过新对话发送消息
2. 前端请求生成新对话
3. 后端返回对话ID
4. 前端根据消息中的图片，请求预签名上传url(带有用户ID和对话ID)
5. 后端生成cos_key和预签名上传url，返回前端
6. 前端通过预签名上传url上传图片
7. 前端同时请求生成对话标题和获取AI回复
8. 后端接收消息，从消息中的预签名上传url中提取出cos_key，生成预签名下载url，输入模型
9. 后端返回对话标题和AI回复
### 聊天时
1. 用户上传图片
2. 前端根据消息中的图片，请求预签名上传url
3. 后端生成cos_key和预签名上传url，返回前端
4. 前端通过预签名上传url上传图片
5. 前端将消息列表发给后端，请求AI回复
6. 后端接收消息，从消息中的预签名上传url中提取出cos_key ，替换为预签名下载url，输入模型
7. 后端返回AI回复
### 加载消息历史时
1. 加载历史消息时，后端将消息中的cos_key替换为预签名下载url，发给前端
2. 前端获取消息，用预签名下载url下载图片

## 日志管理
1. 中间件获取请求头中的信息，存入上下文变量  
   包括:
   - request_id
   - trace_id
   - client_ip
   - method
   - path
2. 从上下文变量中获取信息，和消息一并写入日志  
   最终日志文件格式如下:
   ```json
   {
      "time": "xxx",
      "level": "xxx",
      "request_id": "xxx",
      "trace_id": "xxx",
      "client_ip": "xxx",
      "method": "xxx",
      "path": "xxx",
      "message": "xxx"
   }
   ```