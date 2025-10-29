import { defineConfig, mergeConfig } from 'vite';
import base from './vite.config.js';
export default mergeConfig(base, defineConfig({
  server: {
    host: true,
    port: 5174,
    strictPort: true,
    allowedHosts: 'all', // 개발환경에서 모든 호스트 허용
    hmr: {
      protocol: 'ws', // 개발환경에서는 http 사용
      host: 'localhost',
      clientPort: 80,
      port: 5174,
      path: '/hmr'
    }
  },
  preview: { host: true, port: 5174, strictPort: true, allowedHosts: 'all' },
}));
