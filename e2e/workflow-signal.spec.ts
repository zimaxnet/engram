import { test, expect } from '@playwright/test'

test.describe('Workflow Signals', () => {
  test('should display workflow detail and allow sending signals', async ({ page }) => {
    // Navigate to a workflow detail page
    // In a real scenario, we'd start a workflow first, but for testing we'll use a mock workflow ID
    await page.goto('/workflows/test-workflow-123')

    // Wait for workflow detail to load
    await expect(page.getByRole('heading', { name: /workflow detail/i })).toBeVisible({ timeout: 10000 })

    // Verify workflow ID is displayed
    await expect(page.getByText(/test-workflow-123/i)).toBeVisible()

    // Verify signals section is displayed
    await expect(page.getByRole('heading', { name: /signals/i })).toBeVisible()

    // Verify signal buttons are present
    await expect(page.getByRole('button', { name: /approve/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /provide input/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /cancel/i })).toBeVisible()
  })

  test('should navigate to telemetry from workflow detail', async ({ page }) => {
    await page.goto('/workflows/test-workflow-123')

    // Wait for workflow detail to load
    await expect(page.getByRole('heading', { name: /workflow detail/i })).toBeVisible({ timeout: 10000 })

    // Click open in telemetry button
    const telemetryButton = page.getByRole('button', { name: /open in telemetry/i })
    await telemetryButton.click()

    // Should navigate to evidence page
    await expect(page).toHaveURL(/\/evidence/, { timeout: 5000 })
  })
})

