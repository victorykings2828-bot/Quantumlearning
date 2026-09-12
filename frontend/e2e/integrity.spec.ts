import { expect, test } from '@playwright/test';
import { ensureSession } from './helpers';

test.describe('honesty and isolation', () => {
  test('later chapters are Coming soon and have no working route', async ({ page }) => {
    await page.goto('/course');
    await ensureSession(page);
    await expect(page.getByText('Coming soon').first()).toBeVisible();
    // "Locked" must not appear as a status anywhere on the chapter map.
    await expect(page.getByText('Locked', { exact: true })).toHaveCount(0);

    await page.goto('/course/chapter-6');
    await expect(page.getByRole('heading', { name: /not built yet/i })).toBeVisible();
  });

  test('an unknown route does not show fake functional content', async ({ page }) => {
    await page.goto('/learn/chapter-1/9-9');
    await expect(page.getByRole('heading', { name: /no such topic/i })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Run' })).toHaveCount(0);

    await page.goto('/nonsense-route');
    await expect(page.getByRole('heading', { name: /nothing at this address/i })).toBeVisible();
  });

  test('no answer key or rubric reaches the browser', async ({ page }) => {
    const leaked: string[] = [];
    page.on('response', async (response) => {
      if (!response.url().includes('/api/v1/')) return;
      const type = response.headers()['content-type'] ?? '';
      if (!type.includes('json')) return;
      const body = await response.text().catch(() => '');
      for (const marker of [
        'answer_key',
        'revision_guidance',
        '"rubrics"',
        'essential_item_numbers"]',
      ]) {
        if (body.includes(marker)) leaked.push(`${response.url()} contains ${marker}`);
      }
    });
    await page.goto('/');
    await page.goto('/course');
    await page.goto('/learn/chapter-1/1-7');
    await page.goto('/assessments/chapter-1');
    await page.waitForLoadState('networkidle');
    expect(leaked).toEqual([]);
  });

  test("another guest cannot read this guest's run", async ({ page, browser }) => {
    await page.goto('/learn/chapter-1/1-4');
    await ensureSession(page);
    await page.getByRole('button', { name: 'X', exact: true }).click();
    await page
      .getByRole('button', { name: /^(Run|New preparation)$/ })
      .first()
      .click();
    await expect(page.getByText(/State after step/)).toBeVisible({ timeout: 20_000 });

    const runId = await page.evaluate(async () => {
      const response = await fetch('/api/v1/topics/1-4/runs', { credentials: 'same-origin' });
      const body = await response.json();
      return body.runs[0].run_id as string;
    });
    expect(runId).toBeTruthy();

    const other = await browser.newContext();
    const otherPage = await other.newPage();
    await otherPage.goto('/');
    await expect
      .poll(
        async () =>
          (await other.cookies()).some(
            (c) => c.name === (process.env.E2E_SESSION_COOKIE ?? 'qll_session'),
          ),
        {
          timeout: 15_000,
        },
      )
      .toBe(true);
    const status = await otherPage.evaluate(async (id) => {
      const response = await fetch(`/api/v1/runs/${id}`, { credentials: 'same-origin' });
      return response.status;
    }, runId);
    expect(status).toBe(404);
    await other.close();
  });

  test('a second guest has separate progress', async ({ page, browser }) => {
    await page.goto('/learn/chapter-1/1-1');
    await ensureSession(page);
    await page.getByRole('checkbox').first().check();
    await page.reload();
    await expect(page.getByRole('checkbox').first()).toBeChecked();

    const other = await browser.newContext();
    const otherPage = await other.newPage();
    await otherPage.goto('/learn/chapter-1/1-1');
    await expect(otherPage.getByRole('checkbox').first()).not.toBeChecked();
    await other.close();
  });

  test('Grover overshoot is visible and labelled honestly', async ({ page }) => {
    await page.goto('/lab/grover');
    await ensureSession(page);
    await expect(page.getByText('Analytical prediction').first()).toBeVisible();

    await page.getByLabel('Search space').selectOption('8');
    await page.getByLabel('Grover iterations').fill('2');
    await page.getByRole('button', { name: 'Run', exact: true }).click();
    await expect(page.getByText(/State after step/)).toBeVisible({ timeout: 20_000 });
    const twoText = await page
      .getByText(/Exact target probability from the simulated circuit/)
      .textContent();

    await page.getByLabel('Grover iterations').fill('3');
    await page.getByRole('button', { name: 'Run', exact: true }).click();
    await expect
      .poll(
        async () =>
          (await page
            .getByText(/Exact target probability from the simulated circuit/)
            .textContent()) ?? '',
        { timeout: 25_000 },
      )
      .toContain('0.330078');
    // Three iterations overshoot the peak reached at two.
    expect(twoText).toContain('0.945312');
  });

  test('the missing-preparation variant is marked outside the formula', async ({ page }) => {
    await page.goto('/lab/grover');
    await ensureSession(page);
    await page.getByLabel('Initial preparation').selectOption('missing');
    await expect(page.getByText(/outside the standard success formula/i).first()).toBeVisible();
    await page.getByRole('button', { name: 'Run', exact: true }).click();
    await expect(page.getByText(/does not apply to it/i)).toBeVisible({ timeout: 20_000 });
  });

  test('the Shor preview stays conceptual', async ({ page }) => {
    await page.goto('/lab/shor');
    await ensureSession(page);
    await expect(page.getByText(/No Shor circuit is executed/)).toBeVisible();
    await expect(page.getByRole('button', { name: 'Run', exact: true })).toHaveCount(0);
    // The modular-power table is classical arithmetic, computed on the server.
    await expect(page.getByRole('cell', { name: '8', exact: true }).first()).toBeVisible();
  });
});
