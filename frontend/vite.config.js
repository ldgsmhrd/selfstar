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
      '/api':  { target: 'http://backend:8000', changeOrigin: true, secure: false },
      '/user': { target: 'http://backend:8000', changeOrigin: true, secure: false }, // legacy
      '/personas': { target: 'http://backend:8000', changeOrigin: true, secure: false },
      '/media':{ target: 'http://backend:8000', changeOrigin: true, secure: false },
    },
  },
}) 