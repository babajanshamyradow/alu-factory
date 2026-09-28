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
    port: 5173,
    proxy: {
      // Same-origin dev proxy to the Flask backend (CRM_PORT in backend/config.ini)
      // so the session cookie set by /login is treated as first-party by the
      // browser — avoids needing flask-cors entirely.
      //
      // Auth endpoints are matched exactly (a plain '/me' key is a prefix and
      // would also swallow SPA routes like /menu). /login is both a backend
      // endpoint and an SPA route, so browser page loads (Accept: text/html,
      // e.g. F5 on /login) are left to Vite to serve index.html.
      '^/(login|logout|auth-check|me)$': {
        target: 'http://localhost:8888',
        changeOrigin: true,
        bypass: (req) => (req.headers.accept?.includes('text/html') ? req.url : undefined),
      },
      '/media/': { target: 'http://localhost:8888', changeOrigin: true },
      // Convention: every future admin-facing backend endpoint is namespaced
      // under /api/... so this one proxy entry covers all of them.
      '/api/': { target: 'http://localhost:8888', changeOrigin: true },
    },
  },
})
