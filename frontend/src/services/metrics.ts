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

import { getEvidenceTelemetry as apiGetEvidenceTelemetry } from './api'

export async function getEvidenceTelemetry(rangeLabel: EvidenceTelemetrySnapshot['rangeLabel']): Promise<EvidenceTelemetrySnapshot> {
  const raw = await apiGetEvidenceTelemetry(rangeLabel)

  return {
    rangeLabel: (raw as any).range_label ?? rangeLabel,
    reliability: (raw as any).reliability ?? [],
    ingestion: (raw as any).ingestion ?? [],
    memoryQuality: (raw as any).memory_quality ?? [],
    alerts: ((raw as any).alerts ?? []).map((a: any) => ({
      id: a.id,
      severity: a.severity,
      title: a.title,
      detail: a.detail,
      timeLabel: a.time_label,
      status: a.status,
    })),
    narrative: (raw as any).narrative ?? { elena: '', marcus: '' },
    changes: (raw as any).changes ?? [],
  }
}
