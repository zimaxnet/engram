import { http, HttpResponse } from 'msw'

export const handlers = [
  // BAU endpoints
  http.get('*/api/v1/bau/flows', () => {
    return HttpResponse.json([
      {
        id: 'intake-triage',
        title: 'Intake & triage',
        persona: 'Marcus',
        description: 'Turn requests into plans, milestones, owners, and risk flags.',
        cta: 'Start',
      },
      {
        id: 'policy-qa',
        title: 'Policy Q&A',
        persona: 'Elena',
        description: 'Ask questions and get answers with citations and sensitivity warnings.',
        cta: 'Ask',
      },
      {
        id: 'decision-log',
        title: 'Decision log search',
        persona: 'Elena + Marcus',
        description: 'Recall decisions and provenance across time and projects.',
        cta: 'Search',
      },
    ])
  }),

  http.get('*/api/v1/bau/artifacts', () => {
    return HttpResponse.json([
      {
        id: 'art-1',
        name: 'Meeting notes — Steering Committee',
        ingested_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        chips: ['tenant:zimax', 'project:alpha', 'sensitivity:silver'],
      },
      {
        id: 'art-2',
        name: 'Policy update — Data retention',
        ingested_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
        chips: ['tenant:zimax', 'domain:security', 'sensitivity:gold'],
      },
    ])
  }),

  http.post('*/api/v1/bau/flows/:flowId/start', () => {
    return HttpResponse.json({
      workflow_id: 'wf-test-123',
      session_id: 'session-test-123',
      message: 'BAU flow started',
    })
  }),

  // Metrics endpoints
  http.get('*/api/v1/metrics/evidence', () => {
    return HttpResponse.json({
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
        elena: 'Impact: ingest drift reduces confidence in policy Q&A and increases hallucination risk. Hypothesis: connector auth expiry or filetype drift. Verify: run Golden Thread and compare metadata contracts.',
        marcus: 'Plan: pause SharePoint polling, sample failing docs, confirm credentials. ETA: 45m. If Golden Thread fails, rollback last deploy.',
      },
      changes: [
        { label: 'Deploy', value: 'backend@0461f71 → cfed567' },
        { label: 'Config', value: 'chunk_profile: auto → tables' },
        { label: 'SLO', value: 'parse warn threshold 98%' },
      ],
    })
  }),

  // Validation endpoints
  http.get('*/api/v1/validation/datasets', () => {
    return HttpResponse.json([
      {
        id: 'cogai-thread',
        name: 'Golden Thread Transcript',
        filename: 'cogai-thread.txt',
        hash: 'b3c1…9a2f',
        size_label: '18 KB',
        anchors: ['gh-pages', 'document ingestion', 'Unstructured', '/api/v1/etl/ingest'],
      },
      {
        id: 'sample-policy',
        name: 'Sample Policy Document',
        filename: 'policy-data-retention.pdf',
        hash: 'a18d…10fe',
        size_label: '412 KB',
        anchors: ['retention', 'legal hold', 'PII'],
      },
    ])
  }),

  http.get('*/api/v1/validation/runs/latest', () => {
    return HttpResponse.json(null)
  }),

  http.post('*/api/v1/validation/run', async () => {
    // Simulate async processing
    await new Promise((resolve) => setTimeout(resolve, 100))
    return HttpResponse.json({
      summary: {
        run_id: 'run-test-123',
        dataset_id: 'cogai-thread',
        status: 'PASS',
        checks_total: 8,
        checks_passed: 8,
        started_at: new Date().toISOString(),
        ended_at: new Date().toISOString(),
        duration_ms: 650,
        trace_id: '7c2d…',
        workflow_id: 'wf-abc123',
        session_id: 'session-thread',
      },
      checks: [
        { id: 'SEC-001', name: 'Auth gate', status: 'pass', duration_ms: 80, evidence_summary: '401 → 200 confirmed' },
        { id: 'ETL-001', name: 'Ingest document', status: 'pass', duration_ms: 140, evidence_summary: 'chunks_processed=12' },
        { id: 'ETL-002', name: 'Index chunks to memory', status: 'pass', duration_ms: 200, evidence_summary: 'fact_ids: 12' },
        { id: 'MEM-001', name: 'Memory search hit', status: 'pass', duration_ms: 260, evidence_summary: 'query="gh-pages" hit=3' },
        { id: 'CHAT-001', name: 'Grounded answer', status: 'pass', duration_ms: 320, evidence_summary: 'cited /api/v1/etl/ingest' },
        { id: 'WF-001', name: 'Workflow ordering', status: 'pass', duration_ms: 380, evidence_summary: 'init→enrich→reason→validate→persist' },
        { id: 'VAL-001', name: 'Validation gate', status: 'pass', duration_ms: 440, evidence_summary: 'forced fail → rewritten response' },
        { id: 'EP-001', name: 'Episode transcript', status: 'pass', duration_ms: 500, evidence_summary: 'session=session-thread' },
      ],
      narrative: {
        elena: 'Golden thread passed. Ingestion and retrieval are consistent; provenance and tenant scoping appear intact for this dataset. This supports repeatability and audit readiness.',
        marcus: 'No action items. Next: wire the Sources upload UX to /api/v1/etl/ingest and surface evidence bundles + trace/workflow drilldowns in the Navigator.',
      },
    })
  }),

  // Workflows endpoints
  http.get('*/api/v1/workflows/:workflowId', ({ params }) => {
    const workflowId = params.workflowId as string
    return HttpResponse.json({
      workflow_id: workflowId,
      workflow_type: 'AgentWorkflow',
      status: 'running',
      agent_id: 'elena',
      session_id: 'session-thread',
      started_at: new Date().toISOString(),
      task_summary: 'Agent execution workflow',
      steps: [
        { name: 'initialize_context', status: 'completed', duration_label: '120ms', attempts: 1 },
        { name: 'enrich_memory', status: 'completed', duration_label: '220ms', attempts: 1, meta: 'facts=3 entities=1' },
        { name: 'agent_reasoning', status: 'completed', duration_label: '1.4s', attempts: 2, note: '1 retry due to timeout' },
        { name: 'validate_response', status: 'completed', duration_label: '80ms', attempts: 1 },
        { name: 'persist_memory', status: 'completed', duration_label: '180ms', attempts: 1 },
      ],
      context_snapshot: [
        { k: 'Active agent', v: 'elena' },
        { k: 'Last user message', v: "Why didn't ingestion show up on gh-pages?" },
        { k: 'Retrieved facts', v: '3' },
        { k: 'Validation', v: 'PASS' },
      ],
      trace_id: '7c2d…',
    })
  }),

  http.post('*/api/v1/workflows/:workflowId/signal', () => {
    return HttpResponse.json({ success: true, message: 'Signal sent' })
  }),
]

