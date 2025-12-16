import { test, expect } from '@playwright/test'

const flowsResponse = [
  {
    id: 'intake-triage',
    title: 'Intake & Triage',
    persona: 'Elena',
    description: 'Process incoming requests and route to appropriate workflow',
    cta: 'Start',
  },
  {
    id: 'document-review',
    title: 'Document Review',
    persona: 'Marcus',
    description: 'Review and approve document changes',
    cta: 'Start',
  },
]

const artifactsResponse = [
  {
    id: 'art-1',
    name: 'Meeting Notes',
    ingested_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    chips: ['notes', 'team'],
  },
  {
    id: 'art-2',
    name: 'Policy Update',
    ingested_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    chips: ['policy', 'compliance'],
  },
]

const startFlowResponse = {
  workflow_id: 'wf-test-123',
  status: 'running',
}

test.beforeEach(async ({ page }) => {
  await page.route('**/api/v1/bau/flows', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(flowsResponse) })
  )

  await page.route('**/api/v1/bau/artifacts*', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(artifactsResponse) })
  )

  await page.route('**/api/v1/bau/flows/*/start', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(startFlowResponse) })
  )

  // Mock workflow detail page data
  await page.route('**/api/v1/workflows/*', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 'wf-test-123',
        name: 'Intake & Triage',
        status: 'running',
        started_at: new Date().toISOString(),
      }),
    })
  )
})

test.describe('BAU Flow', () => {
  test('should start intake flow and navigate to workflow detail', async ({ page }) => {
    await page.goto('/bau')

    // Wait for BAU Hub to load
    await expect(page.getByRole('heading', { name: /bau hub/i })).toBeVisible()

    // Wait for flows to load
    await expect(page.getByText(/intake & triage/i)).toBeVisible()

    // Click start button for intake-triage flow
    const startButton = page.getByRole('button', { name: /start/i }).first()
    await startButton.click()

    // Should navigate to workflow detail page
    await expect(page).toHaveURL(/\/workflows\//, { timeout: 5000 })

    // Verify workflow detail page loaded
    await expect(page.getByRole('heading', { name: /workflow detail/i })).toBeVisible()
  })

  test('should display recent artifacts', async ({ page }) => {
    await page.goto('/bau')

    // Wait for artifacts to load
    await expect(page.getByText(/meeting notes/i)).toBeVisible({ timeout: 5000 })
    await expect(page.getByText(/policy update/i)).toBeVisible()
  })
})

