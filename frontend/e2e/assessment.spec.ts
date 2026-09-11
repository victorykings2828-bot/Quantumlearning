import { expect, test } from '@playwright/test';
import { ensureSession } from './helpers';

test.describe('assessment', () => {
  test('a test attempt saves answers, submits, and reports skill-specific revision', async ({
    page,
  }) => {
    await page.goto('/assessments/chapter-1');
    await ensureSession(page);
    await page.getByRole('button', { name: 'Start Form A as a test' }).click();
    await expect(page.getByRole('heading', { name: 'Item 1' })).toBeVisible();

    // Answer item 1 correctly and leave the rest blank.
    const itemOne = page.locator('section.panel').filter({
      has: page.getByRole('heading', { name: 'Item 1' }),
    });
    await itemOne.getByRole('radio', { name: '|1>' }).check();
    await expect(page.getByText(/Answers saved|Saving/)).toBeVisible();

    // A reload must restore the saved answer rather than losing it.
    await page.reload();
    await page.getByRole('button', { name: 'Start Form A as a test' }).click();
    await expect(
      page
        .locator('section.panel')
        .filter({ has: page.getByRole('heading', { name: 'Item 1' }) })
        .getByRole('radio', { name: '|1>' }),
    ).toBeChecked();

    await page.getByRole('button', { name: 'Submit for marking' }).click();
    await expect(page.getByRole('heading', { name: 'Result' })).toBeVisible();
    await expect(page.getByText('Not yet passed')).toBeVisible();
    await expect(page.getByText(/What to revise/)).toBeVisible();
  });

  test('both forms cover the same objectives', async ({ page }) => {
    await page.goto('/assessments/chapter-1');
    await ensureSession(page);
    const skillsFor = async (form: 'A' | 'B') => {
      return page.evaluate(async (target) => {
        const response = await fetch('/api/v1/assessments/chapter-1', {
          credentials: 'same-origin',
        });
        const body = await response.json();
        return body.forms[target].map((item: { assessed_skills: string[] }) =>
          item.assessed_skills.join(','),
        );
      }, form);
    };
    expect(await skillsFor('A')).toEqual(await skillsFor('B'));
  });

  test('a test attempt can be moved to practice by the platform', async ({ page }) => {
    await page.goto('/assessments/chapter-1');
    await ensureSession(page);
    await page.getByRole('button', { name: 'Start Form B as a test' }).click();
    await page.getByRole('button', { name: 'Switch this attempt to practice' }).click();
    await expect(page.getByText('Practice mode')).toBeVisible();
  });
});
