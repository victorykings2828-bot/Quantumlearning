import { request } from '@playwright/test';

/**
 * Fail fast, and say why.
 *
 * Playwright's webServer wait reports only "timed out waiting from
 * config.webServer", which hides whether the API, the database or the web
 * server is the problem. This runs once the servers are up and turns an
 * unusable timeout into a readable error.
 */
export default async function globalSetup() {
  const apiPort = Number(process.env.E2E_API_PORT ?? 8001);
  const webPort = Number(process.env.E2E_WEB_PORT ?? 5174);
  const context = await request.newContext();

  try {
    const ready = await context.get(`http://127.0.0.1:${apiPort}/api/v1/health/ready`);
    if (!ready.ok()) {
      const body = await ready.text();
      throw new Error(
        `The API is running but not ready (HTTP ${ready.status()}). ` +
          `This usually means the database is unreachable or unmigrated. ` +
          `Response: ${body}`,
      );
    }

    // The browser talks to the API through the web server's /api proxy, so
    // check that path too rather than only the API's own port.
    const proxied = await context.get(`http://127.0.0.1:${webPort}/api/v1/health/live`);
    if (!proxied.ok()) {
      throw new Error(
        `The web server does not proxy /api to the backend (HTTP ${proxied.status()}). ` +
          `Check VITE_API_PROXY_TARGET.`,
      );
    }
  } finally {
    await context.dispose();
  }
}
