import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.goto('/');
  await expect(page.getByText('Interactive portfolio demo')).toBeVisible();
});

test('shows all three columns and four live KPI values', async ({page}) => {
  await expect(page.getByRole('heading',{name:'Task board'})).toBeVisible();
  await expect(page.locator('.column')).toHaveCount(3);
  await expect(page.locator('.metric')).toHaveCount(4);
  await expect(page.locator('.metric').nth(0).locator('strong')).toHaveText('7');
  await expect(page.locator('.metric').nth(1).locator('strong')).toHaveText('2');
  await expect(page.locator('.metric').nth(2).locator('strong')).toHaveText('2');
  await expect(page.locator('.metric').nth(3).locator('strong')).toHaveText('28.6%');
});

test('creates a task, moves it to done, and updates KPIs across reloads', async ({page}) => {
  await page.getByRole('button',{name:'New task'}).click();
  await page.getByPlaceholder('e.g. Review onboarding flow').fill('Verify new onboarding');
  await page.getByPlaceholder('Add some context').fill('E2E test item');
  await page.getByRole('dialog').getByRole('button',{name:'Create task'}).click();
  const card=page.locator('article.task-card').filter({hasText:'Verify new onboarding'});
  await expect(card).toBeVisible();
  await expect(page.locator('.metric').nth(0).locator('strong')).toHaveText('8');
  await card.getByRole('combobox',{name:'Move task'}).selectOption('done');
  await expect(page.locator('.metric').nth(2).locator('strong')).toHaveText('3');
  await expect(page.locator('.metric').nth(3).locator('strong')).toHaveText('37.5%');
  await page.reload();
  await expect(page.locator('article.task-card').filter({hasText:'Verify new onboarding'})).toBeVisible();
  await expect(page.locator('.metric').nth(2).locator('strong')).toHaveText('3');
});

test('filters by priority, searches, deletes, and resets the demo',async ({page})=>{
  await page.getByRole('combobox',{name:'Filter priority'}).selectOption('high');
  await expect(page.locator('article.task-card')).toHaveCount(3);
  await page.getByRole('combobox',{name:'Filter priority'}).selectOption('all');
  await page.getByRole('textbox',{name:'Search tasks'}).fill('onboarding sprint');
  await expect(page.locator('article.task-card')).toHaveCount(1);
  const card=page.locator('article.task-card').filter({hasText:'Plan onboarding sprint'});
  page.once('dialog',dialog=>dialog.accept());
  await card.getByRole('button',{name:'Delete Plan onboarding sprint'}).click();
  await expect(page.locator('.metric').nth(0).locator('strong')).toHaveText('6');
  await page.getByRole('button',{name:'Reset demo'}).click();
  await expect(page.locator('.metric').nth(0).locator('strong')).toHaveText('7');
  await expect(page.locator('article.task-card')).toHaveCount(7);
});

test('is usable on a mobile viewport without horizontal overflow',async ({page})=>{
  await page.setViewportSize({width:390,height:844});
  await expect(page.getByRole('button',{name:'New task'})).toBeVisible();
  await expect(page.locator('.column')).toHaveCount(3);
  const dimensions=await page.evaluate(()=>({scrollWidth:document.documentElement.scrollWidth,width:window.innerWidth}));
  expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.width+1);
});
