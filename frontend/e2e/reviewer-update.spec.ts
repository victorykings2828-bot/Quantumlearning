import { test, expect } from '@playwright/test';
import { ensureSession } from './helpers';

test('chapter 2 experiment computes, steps and restores after refresh', async ({ page }) => {
  await page.goto('/course/chapter-2');
  await ensureSession(page);
  await expect(
    page.getByRole('heading', { name: 'Useful ideas — with a quick refresher' }),
  ).toBeVisible();
  await page.goto('/learn/chapter-2/2-4');
  await page.getByLabel('Your prediction').fill('At pi the final result should be one.');
  await page.getByRole('button', { name: 'π', exact: true }).click();
  await page.getByRole('button', { name: 'Save prediction and run' }).click();
  await expect(page.getByRole('button', { name: 'Next step' })).toBeVisible();
  for (let i = 0; i < 3; i++) await page.getByRole('button', { name: 'Next step' }).click();
  await expect(page.getByRole('heading', { name: /Step 3/ })).toBeVisible();
  await page.reload();
  await expect(page.getByRole('button', { name: 'Next step' })).toBeVisible();
  await expect(page.getByLabel('Your prediction')).toHaveValue(
    'At pi the final result should be one.',
  );
});

test('chapter 3 mixture has no fake amplitudes and runs with motion off', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/learn/chapter-3/3-6');
  await ensureSession(page);
  await page.getByLabel('Preparation / experiment').selectOption('B');
  await page.getByLabel('Readout basis').selectOption('X');
  await page.getByLabel('Your prediction').fill('The mixture gives four equal X outcomes.');
  await page.getByRole('button', { name: 'Save prediction and run' }).click();
  await expect(page.getByText('Mixed state: no single amplitude').first()).toBeVisible();
  await expect(page.getByRole('button', { name: 'Play', exact: true })).toBeDisabled();
});

test('explanation persists without an AI key and MCQ alone never passes', async ({ page }) => {
  await page.goto('/evidence/chapter-2');
  await ensureSession(page);
  await page.getByRole('radio', { name: '0.25', exact: true }).check();
  await page.getByRole('textbox').fill('Imaginary means the probability is negative.');
  await page.getByRole('button', { name: 'Save my answer' }).click();
  await expect(page.getByRole('heading', { name: 'Your evidence is saved' })).toBeVisible();
  await expect(
    page.getByText('MCQ: correct. This alone does not establish understanding.'),
  ).toBeVisible();
  await expect(page.getByText(/AI evaluation is not configured/)).toBeVisible();
  await page.reload();
  await page.getByText('Read my response').click();
  await expect(page.getByText('Imaginary means the probability is negative.')).toBeVisible();
});

test('tutor defers future chapters and clears later conversation on return', async ({
  page,
}) => {
  await page.goto('/learn/chapter-2/2-4');
  await ensureSession(page);
  await page.getByRole('button', { name: 'Ask the course tutor' }).click();
  const drawer = page.getByRole('dialog', { name: 'Course tutor' });
  await drawer.getByRole('textbox').fill('How do I create a Bell state?');
  await drawer.getByRole('button', { name: /send|ask/i }).click();
  await expect(drawer.getByText(/This topic is discussed in Chapter 3/)).toBeVisible();
  await page.goto('/learn/chapter-1/1-1');
  await page.getByRole('button', { name: 'Ask the course tutor' }).click();
  await expect(page.getByText(/This topic is discussed in Chapter 3/)).toHaveCount(0);
});

test('phase arrows visibly move between computed steps and tips stay attached', async ({
  page,
}) => {
  await page.emulateMedia({ reducedMotion: 'no-preference' });
  await page.goto('/learn/chapter-2/2-4');
  await ensureSession(page);
  await page.getByRole('button', { name: 'π', exact: true }).click();
  await page
    .getByLabel('Your prediction')
    .fill('The relative phase will reverse the second amplitude.');
  await page.getByRole('button', { name: 'Save prediction and run' }).click();
  await page.getByRole('button', { name: 'Next step' }).click();
  const vector = page.locator('.phase-diagram [data-testid="animated-vector"]').nth(1);
  await expect
    .poll(async () => Number(await vector.locator('line').getAttribute('x2')))
    .toBeCloseTo(55 / Math.sqrt(2), 3);
  await page.getByRole('button', { name: 'Next step' }).click();
  const samples = await vector.evaluate(async (element) => {
    const readings: { x: number; tip: number }[] = [];
    const started = performance.now();
    await new Promise<void>((resolve) => {
      function sample() {
        readings.push({
          x: Number(element.querySelector('line')!.getAttribute('x2')),
          tip: Number(element.querySelector('circle')!.getAttribute('cx')),
        });
        if (performance.now() - started < 850) requestAnimationFrame(sample);
        else resolve();
      }
      requestAnimationFrame(sample);
    });
    return readings;
  });
  expect(samples.filter(({ x }) => x > -35 && x < 35).length).toBeGreaterThan(3);
  expect(samples.every(({ x, tip }) => Math.abs(x - tip) < 0.000001)).toBe(true);
  expect(samples.at(-1)!.x).toBeCloseTo(-55 / Math.sqrt(2), 3);
  await page.getByLabel('Motion', { exact: true }).uncheck();
  await page.getByRole('button', { name: 'Previous', exact: true }).click();
  await expect
    .poll(async () => Number(await vector.locator('line').getAttribute('x2')))
    .toBeCloseTo(55 / Math.sqrt(2), 3);
});
