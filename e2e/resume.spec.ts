import { test, expect } from '@playwright/test';

test.describe('Resume Page', () => {
  test('should load and display header', async ({ page }) => {
    await page.goto('/resume');
    await expect(page.locator('text=Career Journey')).toBeVisible();
    await expect(page.locator('text=Resume').first()).toBeVisible();
  });

  test('should display experience section', async ({ page }) => {
    await page.goto('/resume');
    await expect(page.locator('h2', { hasText: 'Experience' })).toBeVisible();
  });

  test('should display charts section', async ({ page }) => {
    await page.goto('/resume');
    await expect(page.locator('h2', { hasText: 'At a Glance' })).toBeVisible();
  });

  test('should display education section', async ({ page }) => {
    await page.goto('/resume');
    await expect(page.locator('h2', { hasText: 'Education' })).toBeVisible();
  });
});
