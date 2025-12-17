/**
 * Lightweight client for Unstructured intake and ingestion metadata.
 * Sources API now wired to backend /api/v1/etl endpoints. Falls back to empty lists on error.
 */
export type IngestStatus = 'healthy' | 'indexing' | 'paused' | 'error'
export type IngestKind = 'Upload' | 'S3' | 'SharePoint' | 'Drive' | 'Email'

export interface IngestSource {
  id: string
  name: string
  kind: IngestKind
  status: IngestStatus
  lastRun: string
  docs: number
  tags: string[]
  errorMessage?: string
}

export interface IngestQueueItem {
  id: string
  name: string
  summary: string
  status: 'running' | 'completed' | 'paused'
  etaLabel: string
}

export interface CreateSourcePayload {
  name: string
  kind: IngestKind
  scope?: string
  tags?: string[]
  retainTables?: boolean
  chunkHint?: string
  roles?: string[]
}

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8082'
const API_VERSION = '/api/v1'

const toSource = (s: any): IngestSource => ({
  id: s.id,
  name: s.name,
  kind: s.kind as IngestKind,
  status: (s.status as IngestStatus) ?? 'healthy',
  lastRun: s.last_run ?? '—',
  docs: Number(s.docs ?? 0),
  tags: Array.isArray(s.tags) ? s.tags : [],
  errorMessage: s.error_message || s.last_error,
})

const toQueueItem = (q: any): IngestQueueItem => ({
  id: q.id,
  name: q.name,
  summary: q.summary ?? '',
  status: q.status ?? 'running',
  etaLabel: q.eta_label ?? '—',
})

export async function listSources(): Promise<IngestSource[]> {
  try {
    const res = await fetch(`${API_BASE}${API_VERSION}/etl/sources`)
    if (!res.ok) throw new Error('Failed to list sources')
    const data = await res.json()
    return Array.isArray(data.sources) ? data.sources.map(toSource) : []
  } catch (err) {
    console.warn('listSources fallback (empty):', err)
    return []
  }
}

export async function createSource(payload: CreateSourcePayload): Promise<IngestSource> {
  const res = await fetch(`${API_BASE}${API_VERSION}/etl/sources`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error('Failed to create source')
  const data = await res.json()
  return toSource(data)
}

export async function listIngestQueue(): Promise<IngestQueueItem[]> {
  try {
    const res = await fetch(`${API_BASE}${API_VERSION}/etl/queue`)
    if (!res.ok) throw new Error('Failed to list queue')
    const data = await res.json()
    return Array.isArray(data.items) ? data.items.map(toQueueItem) : []
  } catch (err) {
    console.warn('listIngestQueue fallback (empty):', err)
    return []
  }
}
