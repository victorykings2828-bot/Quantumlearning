import { defineConfig, devices } from '@playwright/test';

// Explicit local-only validation against the isolated, already-running test copy.
export default defineConfig({
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
      testIgnore: /responsive\.spec\.ts/,
    },
    { name: 'mobile', use: { ...devices['Pixel 5'] }, testMatch: /responsive\.spec\.ts/ },
  ],
  testDir: './e2e',
  workers: 1,
  fullyParallel: false,
  timeout: 60000,
  reporter: 'list',
  use: {
    baseURL: process.env.REVIEW_URL ?? 'http://127.0.0.1:5189',
    launchOptions: { executablePath: process.env.PW_CHROMIUM_PATH },
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
});
