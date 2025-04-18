import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { nodePolyfills } from 'vite-plugin-node-polyfills';
import path from 'path';

// Import plugins
import copyWorkletPlugin from './plugins/copyWorkletPlugin';
import serveWorkletPlugin from './plugins/serveWorkletPlugin';
import corsHeadersPlugin from './plugins/corsHeadersPlugin';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    copyWorkletPlugin,
    react(),
    nodePolyfills({
      include: ['buffer', 'process', 'stream'],
      protocolImports: true,
    }),
    corsHeadersPlugin,
    serveWorkletPlugin
  ],
  optimizeDeps: {
    esbuildOptions: {
      // Node.js global to browser globalThis
      define: {
        global: 'globalThis',
      },
    },
  },
  build: {
    outDir: 'build',
    sourcemap: true,
  },
  server: {
    port: 3000,
  },
  publicDir: 'public'
});