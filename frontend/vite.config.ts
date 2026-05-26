import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    host: '0.0.0.0',
    watch: {
      usePolling: true,
    },
    proxy: {
      '/api/v1/chat/completions': {
        target: 'http://api-dev:8000',
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on('proxyRes', (_proxyRes, _req, res) => {
            res.setHeader('X-Accel-Buffering', 'no')
          })
        },
      },
      '/api': {
        target: 'http://api-dev:8000',
        changeOrigin: true,
      },
    },
  },
})
