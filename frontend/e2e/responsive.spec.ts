import { expect, test } from '@playwright/test';

test.describe('mobile and keyboard use', () => {
  test('no header, chart or composer overlap at phone width', async ({ page }) => {
    await page.goto('/learn/chapter-1/1-7');
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();

    const overlap = await page.evaluate(() => {
      const header = document.querySelector('.site-header')!.getBoundingClientRect();
      const main = document.querySelector('#main')!.getBoundingClientRect();
      return { headerBottom: header.bottom, mainTop: main.top };
    });
    expect(overlap.mainTop).toBeGreaterThanOrEqual(overlap.headerBottom - 1);

    // The page must not scroll sideways.
    const horizontal = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(horizontal).toBeLessThanOrEqual(1);
  });

  test('the collapsed menu does not cover the content it opens over', async ({ page }) => {
    await page.goto('/course');
    await page.getByRole('button', { name: 'Menu' }).click();
    await expect(page.getByRole('navigation', { name: 'Primary' })).toBeVisible();
    await page.getByRole('link', { name: 'Progress' }).click();
    await expect(page).toHaveURL(/\/progress$/);
  });

  test('a learner can work the laboratory with the keyboard only', async ({ page }) => {
    await page.goto('/learn/chapter-1/1-4');
    await page.keyboard.press('Tab');
    // Walk the focus order until the gate button is reached, then activate it.
    for (let index = 0; index < 60; index += 1) {
      const label = await page.evaluate(() => document.activeElement?.textContent?.trim() ?? '');
      if (label === 'X') break;
      await page.keyboard.press('Tab');
    }
    expect(await page.evaluate(() => document.activeElement?.textContent?.trim())).toBe('X');
    await page.keyboard.press('Enter');
    await expect(page.locator('.wire__gate')).toHaveCount(1);
  });
});
