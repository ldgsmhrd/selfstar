import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'

// ESM 환경에서 __dirname 대체
const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { '@': path.resolve(__dirname, './src') } },
  server: {
    port: 5174,
    proxy: {
      // In Docker, the backend is reachable via its service name on the default network
  '/auth': { target: 'http://backend:8000', changeOrigin: true, secure: false },
  // 개발 환경에서 프록시 라우팅: /api/chat -> /chat, /api/files -> /files, /api/instagram -> /instagram
  '/api/chat': { target: 'http://backend:8000', changeOrigin: true, secure: false, rewrite: (p) => p.replace(/^\/api\/chat/, '/chat') },
  '/api/files': { target: 'http://backend:8000', changeOrigin: true, secure: false, rewrite: (p) => p.replace(/^\/api\/files/, '/files') },
  '/api/instagram': { target: 'http://backend:8000', changeOrigin: true, secure: false, rewrite: (p) => p.replace(/^\/api\/instagram/, '/instagram') },
  // 그 외 /api 엔드포인트는 백엔드에서 이미 prefix 포함이므로 그대로 전달 (예: /api/personas, /api/users, /api/images)
  '/api':  { target: 'http://backend:8000', changeOrigin: true, secure: false },
  // Legacy/non-api routes used in dev occasionally
  '/users': { target: 'http://backend:8000', changeOrigin: true, secure: false },
  '/user': { target: 'http://backend:8000', changeOrigin: true, secure: false }, // legacy
  '/personas': { target: 'http://backend:8000', changeOrigin: true, secure: false },
  '/media':{ target: 'http://backend:8000', changeOrigin: true, secure: false },
  // IMPORTANT: Do not proxy SPA routes like /chat; let the frontend router handle refreshes.
    },
  },
}) 