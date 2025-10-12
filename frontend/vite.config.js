import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    open: false,
    proxy: {
      // Optionally forward /api -> backend (uncomment if you later add /api prefix)
      // '/api': {
      //   target: process.env.VITE_API_BASE_URL || 'http://localhost:8000',
      //   changeOrigin: true,
      // }
    }
  }
});
