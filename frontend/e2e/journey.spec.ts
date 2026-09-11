import { expect, test } from '@playwright/test';
import {
  addGates,
  ensureSession,
  exactProbabilities,
  openTopic,
  provenance,
  runCircuit,
} from './helpers';

test.describe('learning journey', () => {
  test('introduction leads to the course overview and then to Topic 1.1', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: /Learn quantum algorithms/ })).toBeVisible();
    await expect(page.getByText(/quantum simulator executing on/i).first()).toBeVisible();
    await ensureSession(page);

    await page.getByRole('link', { name: 'Explore the course' }).click();
    await expect(page).toHaveURL(/\/course$/);
    await expect(
      page.getByRole('heading', { name: 'Quantum Learning Laboratory' }),
    ).toBeVisible();

    await page
      .getByRole('link', { name: /^Start Chapter 1$|^Continue Topic/ })
      .first()
      .click();
    await expect(page).toHaveURL(/\/learn\/chapter-1\//);
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  });

  test('a changed gate changes the computed values and every linked panel', async ({
    page,
  }) => {
    await openTopic(page, '1-5');
    await addGates(page, ['H']);
    await runCircuit(page);
    const equalSplit = await exactProbabilities(page);
    expect(equalSplit[0]).toBeCloseTo(0.5, 6);
    expect(equalSplit[1]).toBeCloseTo(0.5, 6);

    await addGates(page, ['H']);
    await runCircuit(page);
    const restored = await exactProbabilities(page);
    expect(restored[0]).toBeCloseTo(1, 6);
    expect(restored[1]).toBeCloseTo(0, 6);
  });

  test('editing after a run marks the displayed result as no longer current', async ({
    page,
  }) => {
    await openTopic(page, '1-5');
    await addGates(page, ['H']);
    await runCircuit(page);
    await addGates(page, ['H']);
    await expect(
      page.getByText(/circuit has changed since this result was computed/i),
    ).toBeVisible();
    // The stale panel still describes the earlier circuit; it is not relabelled.
    const stale = await exactProbabilities(page);
    expect(stale[0]).toBeCloseTo(0.5, 6);
  });

  test('run, step, replay and a new run keep distinct identities', async ({ page }) => {
    await openTopic(page, '1-3');
    await runCircuit(page);
    const first = await provenance(page).textContent({ timeout: 5_000 });

    await page.getByRole('button', { name: 'Replay' }).click();
    await expect(page.getByText(/not a new measurement/i).first()).toBeVisible();
    // Replay reads the saved run; it does not create a new one.
    expect(await provenance(page).textContent({ timeout: 5_000 })).toBe(first);

    await runCircuit(page);
    expect(await provenance(page).textContent({ timeout: 5_000 })).not.toBe(first);
  });

  test('repeating a recorded measurement is not a fresh shot', async ({ page }) => {
    await openTopic(page, '1-3');
    await runCircuit(page);
    await page.getByRole('button', { name: 'Measure this trajectory again' }).click();
    await expect(page.getByText(/with probability 1/i).first()).toBeVisible();
    await expect(page.getByText(/different operation from a fresh shot/i)).toBeVisible();
  });

  test('task completion and progress survive a reload', async ({ page }) => {
    await openTopic(page, '1-2');
    await page.getByRole('checkbox').first().check();
    const task = page.locator('.task').filter({ hasText: 'Born rule arithmetic' });
    await task.getByLabel('P(0)').fill('0.36');
    await task.getByLabel('P(1)').fill('0.64');
    await task.getByRole('button', { name: 'Check my answer' }).click();
    await expect(task.getByText('checked against the task rubric')).toBeVisible();

    await page.reload();
    await expect(page.getByRole('checkbox').first()).toBeChecked();
    await expect(page.locator('.task[data-passed="true"]').first()).toBeVisible();
  });

  test('an alternative circuit passes a distribution goal', async ({ page }) => {
    await openTopic(page, '1-5');
    // X then H reaches |->, a different state with the same Z distribution.
    await addGates(page, ['X', 'H']);
    await runCircuit(page);
    const task = page.locator('.task').filter({ hasText: 'build a 50/50 distribution' });
    await task.getByRole('button', { name: 'Check my answer' }).click();
    await expect(task.getByText('checked against the task rubric')).toBeVisible();
  });

  test('a hint is recorded as assistance', async ({ page }) => {
    await openTopic(page, '1-2');
    const task = page.locator('.task').filter({ hasText: 'Transfer' }).first();
    await task.getByRole('button', { name: /Show a hint/ }).click();
    await expect(task.getByText(/Assistance recorded: level 1/)).toBeVisible();
    await expect(task.getByText(/Hint 1/)).toBeVisible();
  });

  test('an incorrect prediction does not block the topic', async ({ page }) => {
    await openTopic(page, '1-3');
    await page.getByRole('radio', { name: /Yes, because the probabilities/ }).check();
    await page.getByRole('button', { name: 'Record my prediction' }).click();
    await expect(page.getByText(/never fails the topic/i)).toBeVisible();
  });
});
