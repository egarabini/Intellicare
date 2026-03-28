import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/admin-ui/',
  build: {
    outDir: '../../packages/intellicare-core/intellicare_core/static/admin-ui',
    emptyOutDir: true,
  },
  server: {
    port: 5174,
    proxy: {
      '^/admin(?:/|$)': 'http://localhost:8000',
      '^/health(?:/|$)': 'http://localhost:8000',
    },
  },
})
