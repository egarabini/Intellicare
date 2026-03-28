import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/',
  build: {
    outDir: '../../packages/intellicare-core/intellicare_core/static/portal',
    emptyOutDir: true,
  },
  server: {
    port: 5176,
    proxy: {
      '^/health(?:/|$)': 'http://localhost:8000',
    },
  },
})
