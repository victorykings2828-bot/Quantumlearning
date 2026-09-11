import { expect, test } from '@playwright/test';
import { ensureSession } from './helpers';

test.describe('one and two qubit playground', () => {
  test('a Bell pair shows mixed reduced states and correct wording', async ({ page }) => {
    await page.goto('/lab/playground');
    await ensureSession(page);
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();

    await page
      .locator('li')
      .filter({ has: page.getByRole('heading', { name: 'Bell pair' }) })
      .getByRole('button', { name: 'Load' })
      .click();
    await page.getByRole('button', { name: 'Run', exact: true }).click();
    await expect(page.getByText(/State after step/)).toBeVisible({ timeout: 25_000 });

    // The joint state is (|00> + |11>)/sqrt(2).
    const rows = page.locator('table:has(caption:text("Amplitudes at step")) tbody tr');
    await expect(rows).toHaveCount(4);
    await expect(rows.nth(1).locator('td').nth(2)).toHaveText('0.000000');
    await expect(rows.nth(2).locator('td').nth(2)).toHaveText('0.000000');

    // Each qubit has a mixed reduced state. The reference image's wording is wrong.
    await expect(page.getByText(/mixed reduced state/i).first()).toBeVisible();
    await expect(page.getByText(/no state of their own/i)).toHaveCount(0);
    await expect(page.getByText('Bloch vector length 0.000').first()).toBeVisible();
  });

  test('equal marginals alone are not presented as entanglement', async ({ page }) => {
    await page.goto('/lab/playground');
    await ensureSession(page);
    await page
      .locator('li')
      .filter({ has: page.getByRole('heading', { name: 'Two independent coins' }) })
      .getByRole('button', { name: 'Load' })
      .click();
    await page.getByRole('button', { name: 'Run', exact: true }).click();
    await expect(page.getByText(/State after step/)).toBeVisible({ timeout: 25_000 });

    // A product state: each qubit still has a pure state of its own.
    await expect(page.getByText(/pure reduced state of its own/i).first()).toBeVisible();
    await expect(
      page
        .getByText(/do \*\*not\*\* by themselves|not by themselves demonstrate entanglement/i)
        .first(),
    ).toBeVisible();
  });

  test('the published bounds are stated and enforced', async ({ page }) => {
    await page.goto('/lab/playground');
    await ensureSession(page);
    await expect(page.getByText(/not claims about hardware/i)).toBeVisible();
    const options = await page.getByLabel('Qubits').locator('option').allTextContents();
    expect(options).toEqual(['1', '2']);
  });
});
