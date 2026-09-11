import { expect, type Page } from '@playwright/test';

/** Wait until the guest session cookie exists, so mutations can be authorized. */
export async function ensureSession(page: Page) {
  await expect
    .poll(
      async () => {
        const cookies = await page.context().cookies();
        return cookies.some((cookie) => cookie.name === 'qll_session');
      },
      { timeout: 15_000 },
    )
    .toBe(true);
}

export async function openTopic(page: Page, topicId: string) {
  await page.goto(`/learn/chapter-1/${topicId}`);
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  await ensureSession(page);
}

export async function addGates(page: Page, gates: string[]) {
  for (const gate of gates) {
    await page.getByRole('button', { name: gate, exact: true }).first().click();
  }
}

/** The provenance line identifies the run, so it changes only when a new one arrives. */
export function provenance(page: Page) {
  return page.locator('p.mono').filter({ hasText: 'qiskit-statevector' }).first();
}

export async function runCircuit(page: Page) {
  const before =
    (await provenance(page)
      .textContent()
      .catch(() => null)) ?? '';
  await page
    .getByRole('button', { name: /^(Run|New preparation)$/ })
    .first()
    .click();
  await expect
    .poll(
      async () =>
        (await provenance(page)
          .textContent()
          .catch(() => '')) ?? '',
      {
        timeout: 25_000,
      },
    )
    .not.toBe(before);
}

export async function exactProbabilities(page: Page): Promise<number[]> {
  const rows = page.locator('table:has(caption:text("Exact probabilities beside")) tbody tr');
  await expect(rows.first()).toBeVisible();
  const count = await rows.count();
  const values: number[] = [];
  for (let index = 0; index < count; index += 1) {
    const text = await rows.nth(index).locator('td').nth(1).textContent();
    values.push(Number(text));
  }
  return values;
}
