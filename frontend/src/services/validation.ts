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

import { listGoldenDatasets as apiListGoldenDatasets, getLatestGoldenRun as apiGetLatestGoldenRun, runGoldenThread as apiRunGoldenThread } from './api'

export async function listGoldenDatasets(): Promise<GoldenDataset[]> {
  const datasets = await apiListGoldenDatasets()
  // Map backend response to frontend format
  return datasets.map((d) => ({
    id: d.id as GoldenDatasetId,
    name: d.name,
    filename: d.filename,
    hash: d.hash,
    sizeLabel: d.size_label,
    createdAt: new Date().toISOString(), // Backend doesn't provide createdAt, use current time
    anchors: d.anchors,
  }))
}

export async function getLatestGoldenRun(): Promise<GoldenRun | null> {
  const run = await apiGetLatestGoldenRun()
  if (!run) return null
  
  // Map backend response to frontend format
  return {
    summary: {
      runId: run.summary.run_id,
      datasetId: run.summary.dataset_id as GoldenDatasetId,
      status: run.summary.status,
      checksTotal: run.summary.checks_total,
      checksPassed: run.summary.checks_passed,
      startedAt: run.summary.started_at,
      endedAt: run.summary.ended_at,
      durationMs: run.summary.duration_ms,
      traceId: run.summary.trace_id,
      workflowId: run.summary.workflow_id,
      sessionId: run.summary.session_id,
    },
    checks: run.checks.map((c) => ({
      id: c.id,
      name: c.name,
      status: c.status,
      durationMs: c.duration_ms,
      evidenceSummary: c.evidence_summary,
    })),
    narrative: run.narrative,
  }
}

export interface RunGoldenThreadOptions {
  datasetId: GoldenDatasetId
  mode: 'deterministic' | 'acceptance'
}

export async function runGoldenThread(options: RunGoldenThreadOptions): Promise<GoldenRun> {
  const result = await apiRunGoldenThread(options.datasetId, options.mode)
  
  // Map backend response to frontend format
  return {
    summary: {
      runId: result.summary.run_id,
      datasetId: result.summary.dataset_id as GoldenDatasetId,
      status: result.summary.status,
      checksTotal: result.summary.checks_total,
      checksPassed: result.summary.checks_passed,
      startedAt: result.summary.started_at,
      endedAt: result.summary.ended_at,
      durationMs: result.summary.duration_ms,
      traceId: result.summary.trace_id,
      workflowId: result.summary.workflow_id,
      sessionId: result.summary.session_id,
    },
    checks: result.checks.map((c) => ({
      id: c.id,
      name: c.name,
      status: c.status,
      durationMs: c.duration_ms,
      evidenceSummary: c.evidence_summary,
    })),
    narrative: result.narrative,
  }
}
