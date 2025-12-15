import { test, expect } from '@playwright/test'

const datasetsResponse = [
  {
    id: 'cogai-thread',
    name: 'Golden Thread Transcript',
    filename: 'cogai-thread.txt',
    hash: 'b3c1-9a2f',
    size_label: '18 KB',
    anchors: ['gh-pages', 'document ingestion', 'Unstructured', '/api/v1/etl/ingest'],
  },
  {
    id: 'sample-policy',
    name: 'Sample Policy Document',
    filename: 'policy-data-retention.pdf',
    hash: 'a18d-10fe',
    size_label: '412 KB',
    anchors: ['retention', 'legal hold', 'PII'],
  },
]

const runResponse = {
  summary: {
    run_id: 'run-test-123',
    dataset_id: 'cogai-thread',
    status: 'PASS',
    checks_total: 8,
    checks_passed: 8,
    started_at: new Date().toISOString(),
    ended_at: new Date().toISOString(),
    duration_ms: 650,
    trace_id: 'trace-7c2d',
    workflow_id: 'wf-abc123',
    session_id: 'session-thread',
  },
  checks: [
    { id: 'SEC-001', name: 'Auth gate', status: 'pass', duration_ms: 80, evidence_summary: '401 -> 200 confirmed' },
    { id: 'ETL-001', name: 'Ingest document', status: 'pass', duration_ms: 140, evidence_summary: 'chunks_processed=12' },
    { id: 'ETL-002', name: 'Index chunks to memory', status: 'pass', duration_ms: 200, evidence_summary: 'fact_ids: 12' },
    { id: 'MEM-001', name: 'Memory search hit', status: 'pass', duration_ms: 260, evidence_summary: 'query="gh-pages" hit=3' },
    { id: 'CHAT-001', name: 'Grounded answer', status: 'pass', duration_ms: 320, evidence_summary: 'cited /api/v1/etl/ingest' },
    { id: 'WF-001', name: 'Workflow ordering', status: 'pass', duration_ms: 380, evidence_summary: 'init->enrich->reason->validate->persist' },
    { id: 'VAL-001', name: 'Validation gate', status: 'pass', duration_ms: 440, evidence_summary: 'forced fail -> rewritten response' },
    { id: 'EP-001', name: 'Episode transcript', status: 'pass', duration_ms: 500, evidence_summary: 'session=session-thread' },
  ],
  narrative: {
    elena: 'Golden thread passed. Ingestion and retrieval are consistent; provenance and tenant scoping appear intact for this dataset.',
    marcus: 'Next: wire the Sources upload UX to /api/v1/etl/ingest and surface evidence bundles in the Navigator.',
  },
}

test.beforeEach(async ({ page }) => {
  await page.route('**/api/v1/validation/datasets', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(datasetsResponse) })
  )

  await page.route('**/api/v1/validation/runs/latest', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: 'null' })
  )

  await page.route('**/api/v1/validation/run', async (route) => {
    if (route.request().method().toUpperCase() === 'POST') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(runResponse) })
    }
    return route.continue()
  })
})

test.describe('Golden Thread Runner', () => {
  test('should run golden thread suite and display results', async ({ page }) => {
    await page.goto('/validation/golden-thread')

    // Wait for page to load
    await expect(page.getByRole('heading', { name: /golden thread/i })).toBeVisible()

    // Verify datasets are loaded
    const datasetSelect = page.getByLabel(/dataset/i)
    await expect(datasetSelect).toBeVisible()
    await expect(datasetSelect).toHaveValue('cogai-thread')

    // Click run suite button
    const runButton = page.getByRole('button', { name: /run suite/i })
    await runButton.click()

    // Wait for run to complete (PASS status)
    await expect(page.getByText('PASS').first()).toBeVisible({ timeout: 10000 })

    // Verify evidence IDs are displayed
    await expect(page.getByText('Workflow ID').first()).toBeVisible()
    await expect(page.getByText('Session ID').first()).toBeVisible()
    await expect(page.getByText('Trace ID').first()).toBeVisible()

    // Verify checks are displayed
    await expect(page.getByText(/auth gate/i)).toBeVisible()
    await expect(page.getByText(/ingest document/i)).toBeVisible()
  })
})

