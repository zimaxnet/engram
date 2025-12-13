export type GoldenDatasetId = 'cogai-thread' | 'sample-policy' | 'sample-meeting-notes' | 'sample-ticket-export'

export interface GoldenDataset {
  id: GoldenDatasetId
  name: string
  filename: string
  hash: string
  sizeLabel: string
  createdAt: string
  anchors: string[]
}

export type GoldenCheckStatus = 'pending' | 'running' | 'pass' | 'fail' | 'warn'

export interface GoldenCheck {
  id: string
  name: string
  status: GoldenCheckStatus
  durationMs?: number
  evidenceSummary?: string
  details?: Record<string, unknown>
}

export interface GoldenRunSummary {
  runId: string
  datasetId: GoldenDatasetId
  status: 'PASS' | 'FAIL' | 'WARN' | 'RUNNING'
  checksTotal: number
  checksPassed: number
  startedAt: string
  endedAt?: string
  durationMs?: number
  traceId?: string
  workflowId?: string
  sessionId?: string
}

export interface GoldenRun {
  summary: GoldenRunSummary
  checks: GoldenCheck[]
  narrative: {
    elena: string
    marcus: string
  }
}

const nowIso = () => new Date().toISOString()

const datasets: GoldenDataset[] = [
  {
    id: 'cogai-thread',
    name: 'Golden Thread Transcript',
    filename: 'cogai-thread.txt',
    hash: 'b3c1…9a2f',
    sizeLabel: '18 KB',
    createdAt: '2025-12-12T22:41:00Z',
    anchors: ['gh-pages', 'document ingestion', 'Unstructured', '/api/v1/etl/ingest'],
  },
  {
    id: 'sample-policy',
    name: 'Sample Policy Document',
    filename: 'policy-data-retention.pdf',
    hash: 'a18d…10fe',
    sizeLabel: '412 KB',
    createdAt: '2025-12-01T10:05:00Z',
    anchors: ['retention', 'legal hold', 'PII'],
  },
  {
    id: 'sample-meeting-notes',
    name: 'Sample Meeting Notes',
    filename: 'steering-committee-notes.docx',
    hash: '55d2…c0aa',
    sizeLabel: '96 KB',
    createdAt: '2025-12-03T16:22:00Z',
    anchors: ['decision', 'milestone', 'risk'],
  },
  {
    id: 'sample-ticket-export',
    name: 'Sample Ticket Export',
    filename: 'service-desk-export.csv',
    hash: '9b02…7e12',
    sizeLabel: '1.2 MB',
    createdAt: '2025-11-18T09:11:00Z',
    anchors: ['incident', 'priority', 'SLA'],
  },
]

let lastRun: GoldenRun | null = null

export async function listGoldenDatasets(): Promise<GoldenDataset[]> {
  return datasets.map((d) => ({ ...d, anchors: [...d.anchors] }))
}

function buildChecks(status: GoldenCheckStatus): GoldenCheck[] {
  const mk = (id: string, name: string, evidenceSummary?: string): GoldenCheck => ({
    id,
    name,
    status,
    evidenceSummary,
  })

  return [
    mk('SEC-001', 'Auth gate', '401 → 200 confirmed'),
    mk('ETL-001', 'Ingest document', 'chunks_processed=12'),
    mk('ETL-002', 'Index chunks to memory', 'fact_ids: 12'),
    mk('MEM-001', 'Memory search hit', 'query="gh-pages" hit=3'),
    mk('CHAT-001', 'Grounded answer', 'cited /api/v1/etl/ingest'),
    mk('WF-001', 'Workflow ordering', 'init→enrich→reason→validate→persist'),
    mk('VAL-001', 'Validation gate', 'forced fail → rewritten response'),
    mk('EP-001', 'Episode transcript', 'session=session-thread'),
  ]
}

export async function getLatestGoldenRun(): Promise<GoldenRun | null> {
  return lastRun
}

export interface RunGoldenThreadOptions {
  datasetId: GoldenDatasetId
  mode: 'deterministic' | 'acceptance'
}

export async function runGoldenThread(options: RunGoldenThreadOptions): Promise<GoldenRun> {
  const startedAt = nowIso()
  const runId = `run-${Date.now()}`

  // Start with "running" checks
  const running: GoldenRun = {
    summary: {
      runId,
      datasetId: options.datasetId,
      status: 'RUNNING',
      checksTotal: 8,
      checksPassed: 0,
      startedAt,
      traceId: '7c2d…',
      workflowId: 'wf-abc123',
      sessionId: 'session-thread',
    },
    checks: buildChecks('running'),
    narrative: {
      elena: 'Running validation…',
      marcus: 'Running validation…',
    },
  }

  lastRun = running

  // Simulate progression
  await new Promise((r) => setTimeout(r, 650))

  const endedAt = nowIso()
  const durationMs = new Date(endedAt).getTime() - new Date(startedAt).getTime()

  const checks = buildChecks('pass').map((c, idx) => ({
    ...c,
    durationMs: 80 + idx * 60,
    details: {
      evidence: c.evidenceSummary,
      datasetId: options.datasetId,
      mode: options.mode,
    },
  }))

  const final: GoldenRun = {
    summary: {
      ...running.summary,
      status: 'PASS',
      checksPassed: 8,
      endedAt,
      durationMs,
    },
    checks,
    narrative: {
      elena:
        'Golden thread passed. Ingestion and retrieval are consistent; provenance and tenant scoping appear intact for this dataset. This supports repeatability and audit readiness.',
      marcus:
        'No action items. Next: wire the Sources upload UX to /api/v1/etl/ingest and surface evidence bundles + trace/workflow drilldowns in the Navigator.',
    },
  }

  lastRun = final
  return final
}
