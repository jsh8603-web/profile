import { test, expect } from '@playwright/test';

test.describe('Contact Page', () => {
  test('should load and display header', async ({ page }) => {
    await page.goto('/contact');
    await expect(page.locator('h1', { hasText: "Let's connect." })).toBeVisible();
    await expect(page.locator('text=Contact').first()).toBeVisible();
  });

  test('should display contact items', async ({ page }) => {
    await page.goto('/contact');
    await expect(page.locator('text=Email')).toBeVisible();
    await expect(page.locator('text=Phone')).toBeVisible();
    await expect(page.locator('text=Location')).toBeVisible();
  });

  test('should have email link with mailto', async ({ page }) => {
    await page.goto('/contact');
    const emailLink = page.locator('main a[href^="mailto:"]');
    await expect(emailLink).toBeVisible();
  });

  test('should have phone link with tel', async ({ page }) => {
    await page.goto('/contact');
    const phoneLink = page.locator('main a[href^="tel:"]');
    await expect(phoneLink).toBeVisible();
  });
});
