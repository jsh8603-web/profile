import { test, expect } from '@playwright/test';

const SKILL_SLUGS = [
  'fpa',
  'project-financing',
  'valuation-ma',
  'systems',
  'leadership',
  'industries',
] as const;

const SKILL_LABELS: Record<string, string> = {
  'fpa': 'FP&A',
  'project-financing': 'Project Financing',
  'valuation-ma': 'Valuation & M&A',
  'systems': 'Systems',
  'leadership': 'Leadership',
  'industries': 'Industries',
};

test.describe('Skill Cards on Homepage', () => {
  test('should display all 6 skill cards in About section', async ({ page }) => {
    await page.goto('/');
    for (const label of Object.values(SKILL_LABELS)) {
      await expect(page.locator('a', { hasText: label }).first()).toBeVisible();
    }
  });

  test('each skill card should link to the correct slug URL', async ({ page }) => {
    await page.goto('/');
    for (const [slug, label] of Object.entries(SKILL_LABELS)) {
      const card = page.locator(`a[href="/skills/${slug}"]`).first();
      await expect(card).toBeVisible();
      await expect(card).toContainText(label);
    }
  });

  test('clicking FP&A card navigates to /skills/fpa', async ({ page }) => {
    await page.goto('/');
    const fpaCard = page.locator('a[href="/skills/fpa"]').first();
    await expect(fpaCard).toBeVisible();
    await fpaCard.click();
    await expect(page).toHaveURL('/skills/fpa');
  });
});

test.describe('Skill Detail Page — FP&A', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/skills/fpa');
  });

  test('should display skill label as heading', async ({ page }) => {
    await expect(page.locator('h1', { hasText: 'FP&A' })).toBeVisible();
  });

  test('should display skill description', async ({ page }) => {
    await expect(
      page.locator('p', { hasText: 'financial planning and analysis' }).first()
    ).toBeVisible();
  });

  test('should display Related Experience section heading', async ({ page }) => {
    await expect(page.locator('h2', { hasText: 'Related Experience' })).toBeVisible();
  });

  test('should display at least one Related Experience card', async ({ page }) => {
    const cards = page.locator('h3', { hasText: 'Coupang' });
    await expect(cards.first()).toBeVisible();
  });

  test('should display Key Achievements section heading', async ({ page }) => {
    await expect(page.locator('h2', { hasText: 'Key Achievements' })).toBeVisible();
  });

  test('should display at least one achievement item', async ({ page }) => {
    await expect(
      page.locator('li span', { hasText: 'costing model' }).first()
    ).toBeVisible();
  });

  test('should display Tools & Skills section heading', async ({ page }) => {
    await expect(page.locator('h2', { hasText: 'Tools & Skills' })).toBeVisible();
  });

  test('should display at least one tool badge', async ({ page }) => {
    await expect(page.locator('span', { hasText: 'SAP' }).first()).toBeVisible();
  });

  test('back link should navigate to /', async ({ page }) => {
    const backLink = page.locator('a', { hasText: 'Back' }).first();
    await expect(backLink).toBeVisible();
    await backLink.click();
    await expect(page).toHaveURL('/');
  });
});

test.describe('All Skill Detail Pages load without error', () => {
  for (const slug of SKILL_SLUGS) {
    test(`/skills/${slug} should load and display the correct label`, async ({ page }) => {
      await page.goto(`/skills/${slug}`);
      const label = SKILL_LABELS[slug];
      await expect(page.locator('h1', { hasText: label })).toBeVisible();
    });
  }
});

test.describe('Not-found skill slug shows error state', () => {
  test('should display Skill not found message for unknown slug', async ({ page }) => {
    await page.goto('/skills/unknown-skill-xyz');
    await expect(page.locator('h1', { hasText: 'Skill not found' })).toBeVisible();
    await expect(
      page.locator('p', { hasText: "doesn't exist" }).first()
    ).toBeVisible();
  });

  test('Back to Home link on error page should navigate to /', async ({ page }) => {
    await page.goto('/skills/unknown-skill-xyz');
    const backLink = page.locator('a', { hasText: 'Back to Home' });
    await expect(backLink).toBeVisible();
    await backLink.click();
    await expect(page).toHaveURL('/');
  });
});
