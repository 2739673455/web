# 聊天前端
项目使用 pnpm 作为包管理器。可以通过 corepack 启用
```bash
corepack enable
corepack prepare pnpm@latest --activate
```

安装依赖
```bash
pnpm install
```

开发模式
```bash
pnpm dev
```

构建生产版本
```bash
pnpm build
```

Vite 配置了 API 代理，将 `/api` 请求转发到后端服务。修改 `vite.config.ts` 中的 `target` 以指向后端地址:
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:12321', // 后端地址
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api/, '')
  }
}
```
