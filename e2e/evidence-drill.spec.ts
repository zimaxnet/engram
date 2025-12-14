import { test, expect } from '@playwright/test'

test.describe('Evidence Telemetry', () => {
  test('should display evidence telemetry with alerts', async ({ page }) => {
    await page.goto('/evidence')

    // Wait for page to load
    await expect(page.getByRole('heading', { name: /evidence & telemetry/i })).toBeVisible()

    // Verify metrics are displayed
    await expect(page.getByText(/reliability/i)).toBeVisible()
    await expect(page.getByText(/ingestion/i)).toBeVisible()
    await expect(page.getByText(/memory quality/i)).toBeVisible()

    // Verify alerts are displayed
    await expect(page.getByText(/parse failures elevated/i)).toBeVisible()
    await expect(page.getByText(/provenance coverage drifting/i)).toBeVisible()

    // Verify narratives
    await expect(page.getByText(/^Elena$/)).toBeVisible()
    await expect(page.getByText(/^Marcus$/)).toBeVisible()
  })

  test('should change range when selector is used', async ({ page }) => {
    await page.goto('/evidence')

    // Wait for page to load
    await expect(page.getByRole('heading', { name: /evidence & telemetry/i })).toBeVisible()

    // Change range selector
    const rangeSelect = page.getByLabel(/range/i)
    await rangeSelect.selectOption('24h')

    // Verify range changed (page should reload data)
    await expect(rangeSelect).toHaveValue('24h')
  })

  test('should navigate to golden thread from evidence page', async ({ page }) => {
    await page.goto('/evidence')

    // Wait for page to load
    await expect(page.getByRole('heading', { name: /evidence & telemetry/i })).toBeVisible()

    // Click run golden thread button
    const goldenThreadButton = page.getByRole('button', { name: /run golden thread/i })
    await goldenThreadButton.click()

    // Should navigate to golden thread page
    await expect(page).toHaveURL(/\/validation\/golden-thread/, { timeout: 5000 })
  })
})

