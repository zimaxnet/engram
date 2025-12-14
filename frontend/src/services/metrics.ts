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
  return apiGetEvidenceTelemetry(rangeLabel)
}
