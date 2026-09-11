import { defineConfig, devices } from '@playwright/test';

/**
 * Browser tests run against the real FastAPI service and a real PostgreSQL
 * database. Only the tutor provider is a test adapter; simulation, evaluation,
 * persistence and the browser interaction are genuine.
 */

const PORT = Number(process.env.E2E_WEB_PORT ?? 5174);
const API_PORT = Number(process.env.E2E_API_PORT ?? 8001);
const baseURL = `http://127.0.0.1:${PORT}`;

const databaseUrl =
  process.env.E2E_DATABASE_URL ??
  'postgresql+psycopg://quantum:quantum_local_only@127.0.0.1:5432/quantum_e2e';

// Locally a preinstalled Chromium may differ from the bundled revision.
const executablePath = process.env.PW_CHROMIUM_PATH || undefined;

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  timeout: 60_000,
  expect: { timeout: 10_000 },
  reporter: process.env.CI ? [['list'], ['html', { open: 'never' }]] : [['list']],
  use: {
    baseURL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'off',
    launchOptions: executablePath ? { executablePath } : {},
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
      testIgnore: /responsive\.spec\.ts/,
    },
    {
      name: 'mobile',
      use: { ...devices['Pixel 5'] },
      testMatch: /responsive\.spec\.ts/,
    },
  ],
  webServer: [
    {
      command: `uv run --frozen uvicorn app.main:app --host 127.0.0.1 --port ${API_PORT}`,
      cwd: '../backend',
      url: `http://127.0.0.1:${API_PORT}/api/v1/health/ready`,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        APP_ENV: 'test',
        DATABASE_URL: databaseUrl,
        SESSION_SECRET: 'e2e-ephemeral-not-a-production-secret',
        PUBLIC_ORIGIN: baseURL,
        COOKIE_SECURE: 'false',
        // An explicit test adapter. This is never presented as a live model.
        TUTOR_PROVIDER: 'authored',
      },
    },
    {
      command: `npm run dev -- --port ${PORT} --strictPort`,
      url: baseURL,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: { VITE_API_PROXY_TARGET: `http://127.0.0.1:${API_PORT}` },
    },
  ],
});
