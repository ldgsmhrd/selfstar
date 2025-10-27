import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    host: true,
    allowedHosts: ['selfstar.duckdns.org'],
    // hmr: { host: 'selfstar.duckdns.org', protocol: 'wss', clientPort: 443 },
  },
  preview: {
    host: true,
    allowedHosts: ['selfstar.duckdns.org'],
  },
});
