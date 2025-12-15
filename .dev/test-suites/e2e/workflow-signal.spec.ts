import { test, expect } from '@playwright/test'

const workflowDetailResponse = {
  workflow_id: 'test-workflow-123',
  workflow_type: 'AgentWorkflow',
  status: 'running',
  agent_id: 'elena',
  session_id: 'session-thread',
  started_at: new Date().toISOString(),
  task_summary: 'Agent execution workflow',
  steps: [
    { name: 'initialize_context', status: 'completed', duration_ms: 120, attempts: 1 },
    { name: 'enrich_memory', status: 'completed', duration_ms: 220, attempts: 1, meta: 'facts=3 entities=1' },
    { name: 'agent_reasoning', status: 'completed', duration_ms: 1400, attempts: 2, note: '1 retry due to timeout' },
    { name: 'validate_response', status: 'completed', duration_ms: 80, attempts: 1 },
    { name: 'persist_memory', status: 'completed', duration_ms: 180, attempts: 1 },
  ],
  context_snapshot: [
    { k: 'Active agent', v: 'elena' },
    { k: 'Last user message', v: "Why didn't ingestion show up on gh-pages?" },
    { k: 'Retrieved facts', v: '3' },
    { k: 'Validation', v: 'PASS' },
  ],
  trace_id: 'trace-7c2d',
}

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
  await page.route('**/api/v1/workflows/test-workflow-123', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(workflowDetailResponse) })
  )

  await page.route('**/api/v1/workflows/test-workflow-123/signal', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ success: true, message: 'Signal sent' }) })
  )

  await page.route('**/api/v1/metrics/evidence', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(metricsResponse) })
  )
})

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

