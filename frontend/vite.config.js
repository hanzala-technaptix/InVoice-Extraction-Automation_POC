import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/invoices': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/gmail': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/pending-invoices': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
