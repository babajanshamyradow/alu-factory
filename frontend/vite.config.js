import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5175,
    proxy: {
      // Same-origin dev proxy to the public site API (SIP_PORT in backend/config.ini).
      '/api/': { target: 'http://localhost:9999', changeOrigin: true },
      '/media/': { target: 'http://localhost:9999', changeOrigin: true },
    },
  },
})
