import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  use: {
    baseURL: 'http://127.0.0.1:4175',
    headless: true,
  },
  webServer: {
    command: 'python -m http.server 4175 -d ../../packages/intellicare-core/intellicare_core/static',
    url: 'http://127.0.0.1:4175/clinico-ui/',
    reuseExistingServer: true,
    timeout: 30_000,
  },
});
