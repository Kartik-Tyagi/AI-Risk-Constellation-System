/**
 * E2E: API error handling
 * Verifies the UI degrades gracefully when backend endpoints return errors.
 */
import { test, expect } from '@playwright/test';

test.describe('API Error Handling', () => {
  test('dashboard handles risk/summary 500 gracefully', async ({ page }) => {
    await page.route(/\/api\/v1\/risk\/summary/, route =>
      route.fulfill({ status: 500, body: JSON.stringify({ detail: 'Internal Server Error' }) })
    );
    await page.route(/\/api\/v1\/risk\/metrics/, route =>
      route.fulfill({ status: 500, body: JSON.stringify({ detail: 'Internal Server Error' }) })
    );
    await page.route(/\/api\/v1\/portfolios/, route =>
      route.fulfill({ status: 500, body: JSON.stringify({ detail: 'Internal Server Error' }) })
    );

    const errors = [];
    page.on('pageerror', err => errors.push(err.message));

    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Page should not crash; main content should be visible
    const main = page.locator('main, #root > *').first();
    await expect(main).toBeVisible();

    const realErrors = errors.filter(e =>
      e && e !== 'Object' &&
      !e.includes('Warning') &&
      !e.includes('ResizeObserver') &&
      !e.includes('AxiosError')
    );
    expect(realErrors).toHaveLength(0);
  });

  test('constellation handles graph 404 gracefully', async ({ page }) => {
    await page.route(/\/api\/v1\/graph/, route =>
      route.fulfill({ status: 404, body: JSON.stringify({ detail: 'Not found' }) })
    );

    const errors = [];
    page.on('pageerror', err => errors.push(err.message));

    await page.goto('/constellation');
    await page.waitForLoadState('networkidle');

    const main = page.locator('main, #root > *').first();
    await expect(main).toBeVisible({ timeout: 10_000 });
  });

  test('portfolio page handles empty portfolio list', async ({ page }) => {
    await page.route(/\/api\/v1\/portfolios/, route =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ portfolios: [], total: 0, page: 1, page_size: 20 }),
      })
    );

    await page.goto('/portfolio');
    await page.waitForLoadState('networkidle');

    const main = page.locator('main, #root > *').first();
    await expect(main).toBeVisible();
  });

  test('network timeout is handled without crashing', async ({ page }) => {
    await page.route(/\/api\/v1\/risk\/summary/, route =>
      route.abort('timedout')
    );

    const errors = [];
    page.on('pageerror', err => errors.push(err.message));

    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Should not show a blank white screen
    const root = page.locator('#root');
    await expect(root).toBeVisible({ timeout: 10_000 });
  });
});
