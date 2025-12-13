export type Severity = 'P0' | 'P1' | 'P2' | 'P3'

export interface MetricCard {
  label: string
  value: string
  status: 'ok' | 'warn' | 'bad'
  note?: string
}

export interface AlertItem {
  id: string
  severity: Severity
  title: string
  detail: string
  timeLabel: string
  status: 'open' | 'closed'
}

export interface EvidenceTelemetrySnapshot {
  rangeLabel: '15m' | '1h' | '24h' | '7d'
  reliability: MetricCard[]
  ingestion: MetricCard[]
  memoryQuality: MetricCard[]
  alerts: AlertItem[]
  narrative: {
    elena: string
    marcus: string
  }
  changes: Array<{ label: string; value: string }>
}

export async function getEvidenceTelemetry(rangeLabel: EvidenceTelemetrySnapshot['rangeLabel']): Promise<EvidenceTelemetrySnapshot> {
  // Deterministic mock snapshot (POC)
  return {
    rangeLabel,
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
    memoryQuality: [
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
        timeLabel: '8m ago',
        status: 'open',
      },
      {
        id: 'a-2',
        severity: 'P3',
        title: 'Provenance coverage drifting',
        detail: 'Some memory results missing filename/source metadata; verify ingestion metadata normalization.',
        timeLabel: '1h ago',
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
      { label: 'Deploy', value: 'backend@0461f71 → cfed567' },
      { label: 'Config', value: 'chunk_profile: auto → tables' },
      { label: 'SLO', value: 'parse warn threshold 98%' },
    ],
  }
}
