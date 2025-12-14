import { test, expect } from '@playwright/test'

test.describe('Golden Thread Runner', () => {
  test('should run golden thread suite and display results', async ({ page }) => {
    await page.goto('/validation/golden-thread')

    // Wait for page to load
    await expect(page.getByRole('heading', { name: /golden thread/i })).toBeVisible()

    // Verify datasets are loaded
    await expect(page.getByText(/golden thread transcript/i)).toBeVisible()

    // Click run suite button
    const runButton = page.getByRole('button', { name: /run suite/i })
    await runButton.click()

    // Wait for run to complete (PASS status)
    await expect(page.getByText('PASS')).toBeVisible({ timeout: 10000 })

    // Verify evidence IDs are displayed
    await expect(page.getByText('Workflow ID')).toBeVisible()
    await expect(page.getByText('Session ID')).toBeVisible()
    await expect(page.getByText('Trace ID')).toBeVisible()

    // Verify checks are displayed
    await expect(page.getByText(/auth gate/i)).toBeVisible()
    await expect(page.getByText(/ingest document/i)).toBeVisible()
  })
})

