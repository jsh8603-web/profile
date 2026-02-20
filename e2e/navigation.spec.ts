import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test('should navigate between all pages via navbar', async ({ page }) => {
    await page.goto('/');

    // Home -> Resume
    await page.locator('nav').getByText('Resume').click();
    await expect(page).toHaveURL('/resume');
    await expect(page.locator('h1', { hasText: 'Career Journey' })).toBeVisible();

    // Resume -> Blog
    await page.locator('nav').getByText('Blog').click();
    await expect(page).toHaveURL('/blog');
    await expect(page.locator('h1', { hasText: 'Insights & Analysis' })).toBeVisible();

    // Blog -> Contact
    await page.locator('nav').getByText('Contact').click();
    await expect(page).toHaveURL('/contact');
    await expect(page.locator('h1', { hasText: "Let's connect." })).toBeVisible();

    // Contact -> Home
    await page.locator('nav').getByText('Home').click();
    await expect(page).toHaveURL('/');
  });

  test('should highlight active nav item', async ({ page }) => {
    await page.goto('/resume');
    const activeLink = page.locator('nav a', { hasText: 'Resume' });
    await expect(activeLink).toHaveClass(/bg-\[#1D1D1F\] text-white/);
  });

  test('should show Sign In link for unauthenticated users', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('nav a', { hasText: 'Sign In' })).toBeVisible();
  });

  test('should show logo linking to home', async ({ page }) => {
    await page.goto('/blog');
    const logo = page.locator('nav a', { hasText: 'SJ' });
    await expect(logo).toBeVisible();
    await logo.click();
    await expect(page).toHaveURL('/');
  });
});
