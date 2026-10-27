import { defineConfig } from '@playwright/test'
export default defineConfig({
  testDir: './e2e', testMatch: 'premium.spec.ts', workers: 1, timeout: 45_000,
  use: { baseURL: 'http://127.0.0.1:5182', browserName: 'chromium', trace: 'retain-on-failure' },
  webServer: { command: 'npm.cmd run dev -- --host 127.0.0.1 --port 5182 --strictPort', url: 'http://127.0.0.1:5182', reuseExistingServer: false },
})
