import { test, expect } from '@playwright/test'

const metricsResponse = {
  range_label: '15m',
  reliability: [
    { label: 'API p95', value: '420ms', status: 'ok' },
    { label: 'Error rate', value: '0.6%', status: 'ok' },
    { label: 'Workflow success', value: '99.2%', status: 'ok', note: 'Warn if < 98%' },
    { label: 'Stuck workflows', value: '0', status: 'ok' },
  ],
  ingestion: [
    { label: 'Parse success', value: '97.8%', status: 'warn', note: 'Warn if < 98%' },
    { label: 'Queue depth', value: '14', status: 'ok' },
    { label: 'Time-to-searchable p95', value: '2.1m', status: 'ok' },
  ],
  memory_quality: [
    { label: 'Retrieval hit-rate', value: '92%', status: 'ok' },
    { label: 'Provenance coverage', value: '88%', status: 'warn' },
    { label: 'Tenant violations', value: '0', status: 'ok' },
  ],
  alerts: [
    {
      id: 'a-1',
      severity: 'P2',
      title: 'Parse failures elevated',
      detail: 'SharePoint source showing increased PDF parse failures; validate OCR strategy and credentials.',
      time_label: '8m ago',
      status: 'open',
    },
    {
      id: 'a-2',
      severity: 'P3',
      title: 'Provenance coverage drifting',
      detail: 'Some memory results missing filename/source metadata; verify ingestion metadata normalization.',
      time_label: '1h ago',
      status: 'open',
    },
  ],
  narrative: {
    elena:
      'Impact: ingest drift reduces confidence in policy Q&A and increases hallucination risk. Hypothesis: connector auth expiry or filetype drift. Verify: run Golden Thread and compare metadata contracts.',
    marcus:
      'Plan: pause SharePoint polling, sample failing docs, confirm credentials. ETA: 45m. If Golden Thread fails, rollback last deploy.',
  },
  changes: [
    { label: 'Deploy', value: 'backend@0461f71 -> cfed567' },
    { label: 'Config', value: 'chunk_profile: auto -> tables' },
    { label: 'SLO', value: 'parse warn threshold 98%' },
  ],
}

test.beforeEach(async ({ page }) => {
  await page.route('**/api/v1/metrics/evidence', (route) => {
    return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(metricsResponse) })
  })
})

test.describe('Evidence Telemetry', () => {
  test('should display evidence telemetry with alerts', async ({ page }) => {
    await page.goto('/evidence')

    // Wait for page to load
    await expect(page.getByRole('heading', { name: /evidence & telemetry/i })).toBeVisible()

    // Verify metrics are displayed
    await expect(page.getByText(/reliability/i)).toBeVisible()
  await expect(page.getByText(/ingestion/i).first()).toBeVisible()
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

