import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  use: {
    baseURL: 'http://localhost:4175/gestor-ui',
    headless: true,
  },
  webServer: {
    command: 'npm run preview',
    url: 'http://localhost:4175/gestor-ui',
    reuseExistingServer: true,
    timeout: 30_000,
  },
});
