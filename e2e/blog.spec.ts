import { test, expect } from '@playwright/test';

test.describe('Blog Page', () => {
  test('should load blog page with header', async ({ page }) => {
    await page.goto('/blog');
    await expect(page.locator('text=Insights & Analysis')).toBeVisible();
    await expect(page.locator('text=Blog').first()).toBeVisible();
  });

  test('should show loading skeleton or posts or empty state', async ({ page }) => {
    await page.goto('/blog');
    // Wait for loading to finish - should show either posts or empty state
    const postsOrEmpty = page.locator('.grid').or(page.locator('text=No posts yet.'));
    await expect(postsOrEmpty.first()).toBeVisible({ timeout: 10000 });
  });

  test('should display category filter', async ({ page }) => {
    await page.goto('/blog');
    // CategoryFilter component should be present with All/Finance/Economy buttons
    const allButton = page.locator('main button', { hasText: 'All' });
    await expect(allButton).toBeVisible();
  });
});

test.describe('Blog Post Page', () => {
  test('should show not found for non-existent post', async ({ page }) => {
    await page.goto('/blog/non-existent-slug-12345');
    await expect(page.locator('text=Post not found')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('a', { hasText: 'Back to Blog' })).toBeVisible();
  });

  test('should navigate back to blog from not found', async ({ page }) => {
    await page.goto('/blog/non-existent-slug-12345');
    await expect(page.locator('text=Post not found')).toBeVisible({ timeout: 10000 });
    await page.locator('a', { hasText: 'Back to Blog' }).click();
    await expect(page).toHaveURL('/blog');
  });
});
