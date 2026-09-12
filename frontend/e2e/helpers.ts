import { expect, type Page } from '@playwright/test';

/** Wait until the guest session cookie exists, so mutations can be authorized. */
export async function ensureSession(page: Page) {
  await expect
    .poll(
      async () => {
        const cookies = await page.context().cookies();
        return cookies.some(
          (cookie) => cookie.name === (process.env.E2E_SESSION_COOKIE ?? 'qll_session'),
        );
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

/**
 * Read the provenance line, or '' when no run exists yet.
 *
 * The explicit timeout matters. Without one, textContent waits indefinitely for
 * an element that has not been rendered, and the catch never runs, so the next
 * action in the test never starts.
 */
export async function provenanceText(page: Page): Promise<string> {
  try {
    return (await provenance(page).textContent({ timeout: 1_000 })) ?? '';
  } catch {
    return '';
  }
}

export async function runCircuit(page: Page) {
  const before = await provenanceText(page);
  await page
    .getByRole('button', { name: /^(Run|New preparation)$/ })
    .first()
    .click();
  await expect.poll(() => provenanceText(page), { timeout: 25_000 }).not.toBe(before);
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
