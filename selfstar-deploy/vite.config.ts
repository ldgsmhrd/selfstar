import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    host: true,
    allowedHosts: ['selfstar.duckdns.org'], // 또는 'all'
  },
  preview: {
    host: true,
    allowedHosts: ['selfstar.duckdns.org'],
  },
});
