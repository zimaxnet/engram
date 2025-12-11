/**
 * Lightweight client for Unstructured intake and ingestion metadata.
 * Currently backed by in-memory mock data so the UI can render without a live API.
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

const seedSources: IngestSource[] = [
  {
    id: 's3-1',
    name: 'S3 - finance-reports',
    kind: 'S3',
    status: 'healthy',
    lastRun: '6m ago',
    docs: 128,
    tags: ['tenant:acme', 'finance', 'gold'],
  },
  {
    id: 'sp-1',
    name: 'SharePoint - PMO',
    kind: 'SharePoint',
    status: 'indexing',
    lastRun: 'Parsing now…',
    docs: 42,
    tags: ['projects', 'pmo'],
  },
  {
    id: 'upl-1',
    name: 'Ad hoc uploads',
    kind: 'Upload',
    status: 'healthy',
    lastRun: 'just now',
    docs: 7,
    tags: ['sandbox', 'demo'],
  },
  {
    id: 'drv-1',
    name: 'Drive - customer-success',
    kind: 'Drive',
    status: 'paused',
    lastRun: 'Yesterday',
    docs: 260,
    tags: ['cs', 'playbooks'],
  },
]

const seedQueue: IngestQueueItem[] = [
  {
    id: 'q-sp',
    name: 'SharePoint - PMO',
    summary: 'Extracting tables • 16 files • serverless',
    status: 'running',
    etaLabel: '1m',
  },
  {
    id: 'q-s3',
    name: 'S3 - finance-reports',
    summary: 'Completed • 128 docs • RBAC: Analysts, Managers',
    status: 'completed',
    etaLabel: 'done',
  },
  {
    id: 'q-drive',
    name: 'Drive - customer-success',
    summary: 'Paused • awaiting approval',
    status: 'paused',
    etaLabel: 'paused',
  },
]

let sourcesState: IngestSource[] = seedSources.map((source) => ({ ...source, tags: [...source.tags] }))

const cloneSources = (items: IngestSource[]) => items.map((item) => ({ ...item, tags: [...item.tags] }))

export async function listSources(): Promise<IngestSource[]> {
  return cloneSources(sourcesState)
}

export async function createSource(payload: CreateSourcePayload): Promise<IngestSource> {
  const next: IngestSource = {
    id: `src-${Date.now()}`,
    name: payload.name,
    kind: payload.kind,
    status: 'indexing',
    lastRun: 'queued',
    docs: 0,
    tags: payload.tags ?? [],
  }

  sourcesState = [next, ...sourcesState]
  return { ...next, tags: [...next.tags] }
}

export async function listIngestQueue(): Promise<IngestQueueItem[]> {
  return seedQueue.map((item) => ({ ...item }))
}
