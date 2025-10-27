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
  // Route /api/chat -> /chat, /api/files -> /files, /api/instagram -> /instagram for dev parity with prod
  '/api/chat': { target: 'http://backend:8000', changeOrigin: true, secure: false, rewrite: (p) => p.replace(/^\/api\/chat/, '/chat') },
  '/api/files': { target: 'http://backend:8000', changeOrigin: true, secure: false, rewrite: (p) => p.replace(/^\/api\/files/, '/files') },
  '/api/instagram': { target: 'http://backend:8000', changeOrigin: true, secure: false, rewrite: (p) => p.replace(/^\/api\/instagram/, '/instagram') },
  // Pass-through for other /api endpoints already prefixed in backend (e.g., /api/personas, /api/users, /api/images)
  '/api':  { target: 'http://backend:8000', changeOrigin: true, secure: false },
  // Legacy/non-api routes used in dev occasionally
  '/users': { target: 'http://backend:8000', changeOrigin: true, secure: false },
  '/user': { target: 'http://backend:8000', changeOrigin: true, secure: false }, // legacy
  '/personas': { target: 'http://backend:8000', changeOrigin: true, secure: false },
  '/media':{ target: 'http://backend:8000', changeOrigin: true, secure: false },
  '/chat': { target: 'http://backend:8000', changeOrigin: true, secure: false },
    },
  },
}) 