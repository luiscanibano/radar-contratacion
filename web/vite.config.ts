import path from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// API routes that live on the FastAPI backend (api/main.py) — proxied in dev
// so the Vite server on :5173 can call the real app without CORS. Scoped to
// exact API sub-paths (not a bare '/billing') so they don't shadow the
// frontend's own /billing/exito and /billing/cancelado pages.
const apiRoutes = [
  '/auth',
  '/me',
  '/buscar',
  '/preguntar',
  '/consultar',
  '/alertas',
  '/billing/checkout',
  '/billing/portal',
  '/billing/webhook',
  '/health',
  '/docs',
  '/openapi.json',
  '/mcp',
]

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: Object.fromEntries(apiRoutes.map((route) => [route, 'http://localhost:8000'])),
  },
  build: {
    rollupOptions: {
      input: {
        landing: path.resolve(__dirname, 'index.html'),
        app: path.resolve(__dirname, 'app/index.html'),
        billingExito: path.resolve(__dirname, 'billing/exito/index.html'),
        billingCancelado: path.resolve(__dirname, 'billing/cancelado/index.html'),
        legal: path.resolve(__dirname, 'legal/index.html'),
      },
    },
  },
})
