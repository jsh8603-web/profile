import { test, expect } from '@playwright/test';

test.describe('Home Page', () => {
  test('should load and display hero section', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Sehoon Jang/);
    const main = page.locator('main');
    await expect(main.locator('text=Financial clarity')).toBeVisible();
    await expect(main.locator('text=drives growth.')).toBeVisible();
    await expect(main.locator('p', { hasText: 'Senior FP&A Manager' }).first()).toBeVisible();
  });

  test('should display navigation bar with all links', async ({ page }) => {
    await page.goto('/');
    const nav = page.locator('nav');
    await expect(nav).toBeVisible();
    await expect(nav.locator('text=Home')).toBeVisible();
    await expect(nav.locator('text=Resume')).toBeVisible();
    await expect(nav.locator('text=Blog')).toBeVisible();
    await expect(nav.locator('text=Contact')).toBeVisible();
  });

  test('should display stats section', async ({ page }) => {
    await page.goto('/');
    const main = page.locator('main');
    await expect(main.getByText('11+', { exact: true })).toBeVisible();
    await expect(main.getByText('Years of Experience')).toBeVisible();
  });

  test('should have working CTA buttons', async ({ page }) => {
    await page.goto('/');
    const viewResume = page.locator('a', { hasText: 'View Resume' });
    await expect(viewResume).toBeVisible();
    await expect(viewResume).toHaveAttribute('href', '/resume');

    const readBlog = page.locator('a', { hasText: 'Read Blog' });
    await expect(readBlog).toBeVisible();
    await expect(readBlog).toHaveAttribute('href', '/blog');
  });

  test('should navigate to Resume via CTA', async ({ page }) => {
    await page.goto('/');
    await page.locator('a', { hasText: 'View Resume' }).click();
    await expect(page).toHaveURL('/resume');
  });

  test('should navigate to Blog via CTA', async ({ page }) => {
    await page.goto('/');
    await page.locator('a', { hasText: 'Read Blog' }).click();
    await expect(page).toHaveURL('/blog');
  });

  test('should display footer', async ({ page }) => {
    await page.goto('/');
    const footer = page.locator('footer');
    await expect(footer).toBeVisible();
  });
});
