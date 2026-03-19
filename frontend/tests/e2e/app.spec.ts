import { test, expect } from '@playwright/test';

test.describe('Doctor Doom Frontend', () => {
  test('should display login page', async ({ page }) => {
    await page.goto('/login');

    await expect(page).toHaveTitle(/Doctor Doom/);
    await expect(page.getByText('Doctor Doom')).toBeVisible();
    await expect(page.getByText('Thermal Panel Inspection System')).toBeVisible();
  });

  test('should show login form', async ({ page }) => {
    await page.goto('/login');

    await expect(page.getByLabel('Email')).toBeVisible();
    await expect(page.getByLabel('Password')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible();
  });

  test('should display demo credentials', async ({ page }) => {
    await page.goto('/login');

    await expect(page.getByText('Demo Credentials:')).toBeVisible();
    await expect(page.getByText('admin@doctor-doom.com')).toBeVisible();
  });
});
