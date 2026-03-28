import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/gestor-ui/',
  build: {
    outDir: '../../packages/intellicare-core/intellicare_core/static/gestor-ui',
    emptyOutDir: true,
  },
  server: {
    port: 5175,
    proxy: {
      '^/gestor(?:/|$)': 'http://localhost:8000',
      '^/vector(?:/|$)': 'http://localhost:8000',
    },
  },
})
