import { defineConfig, mergeConfig } from 'vite';
import base from './vite.config.js';
export default mergeConfig(base, defineConfig({
  server: {
    host: true,
    port: 5174,
    strictPort: true,
    allowedHosts: ['selfstar.duckdns.org'], // 필요 시 'all'
    hmr: {
      protocol: 'wss',
      host: 'selfstar.duckdns.org',
      clientPort: 443,
      port: 443,
      path: '/hmr'
    }
  },
  preview: { host: true, port: 5174, strictPort: true, allowedHosts: ['selfstar.duckdns.org'] },
}));
