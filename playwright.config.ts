import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e',
  testMatch: '**/*.spec.ts',
  timeout: 30_000,
  retries: 1,
  reporter: [['html', { outputFolder: 'tests/e2e/report' }], ['list']],
  use: {
    baseURL: process.env.BASE_URL || 'http://127.0.0.1:9000',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
})

