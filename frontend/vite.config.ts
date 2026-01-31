import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:12321',
        changeOrigin: true,
        rewrite: (path) => {
          // 只移除重复的 /api，保留一个
          return path.replace(/^\/api\/api/, '/api')
        },
        configure: (proxy, options) => {
          proxy.on('proxyRes', (proxyRes, req, res) => {
            // 转发 Set-Cookie header
            const cookies = proxyRes.headers['set-cookie'];
            if (cookies) {
              res.setHeader('set-cookie', cookies);
            }
          });
        },
      },
    },
  },
})