/**
 * Enhanced Ingestion Client with Classification & Connectors
 * ===========================================================
 * Sources API with NIST-aligned classification and Antigravity routing.
 */

export type IngestStatus = 'healthy' | 'indexing' | 'paused' | 'error' | 'pending';

export type IngestKind =
  // Cloud Storage
  | 'S3' | 'AzureBlob' | 'GCS'
  // Collaboration
  | 'SharePoint' | 'GoogleDrive' | 'OneDrive' | 'Confluence'
  // Ticketing
  | 'ServiceNow' | 'Jira' | 'GitHub'
  // Messaging
  | 'Slack' | 'Teams' | 'Email'
  // Data & Integration
  | 'Database' | 'Webhook' | 'Local';

export type SensitivityLevel = 'high' | 'moderate' | 'low';

export type DataCategory =
  | 'pii' | 'phi' | 'cui' | 'pci'
  | 'proprietary' | 'safety' | 'credential'
  | 'public' | 'internal';

export type DataClass = 'CLASS_A_TRUTH' | 'CLASS_B_CHATTER' | 'CLASS_C_OPS';

export type ConnectorCategory =
  | 'cloud_storage'
  | 'collaboration'
  | 'ticketing'
  | 'messaging'
  | 'database'
  | 'local';

export interface IngestSource {
  id: string;
  name: string;
  kind: IngestKind;
  status: IngestStatus;
  lastRun: string;
  docs: number;
  tags: string[];
  errorMessage?: string;
  // New classification fields
  sensitivityLevel?: SensitivityLevel;
  dataCategories?: DataCategory[];
  routingClass?: DataClass;
}

export interface ConnectorMetadata {
  id: string;
  name: string;
  description: string;
  category: ConnectorCategory;
  icon: string;
  defaultClass: DataClass;
  supportedExtensions: string[];
  requiresOauth: boolean;
  requiresApiKey: boolean;
  status: IngestStatus;
  docs: number;
}

export interface IngestQueueItem {
  id: string;
  name: string;
  summary: string;
  status: 'running' | 'completed' | 'paused';
  etaLabel: string;
  // New fields
  dataClass?: DataClass;
  sensitivityLevel?: SensitivityLevel;
}

export interface CreateSourcePayload {
  name: string;
  kind: IngestKind;
  scope?: string;
  tags?: string[];
  retainTables?: boolean;
  chunkHint?: string;
  roles?: string[];
  // New classification fields
  sensitivityLevel?: SensitivityLevel;
  dataCategories?: DataCategory[];
  routingClass?: DataClass;
}

export interface ClassificationResult {
  sensitivityLevel: SensitivityLevel;
  dataCategories: DataCategory[];
  confidence: number;
  decayRate: number;
  requiresEncryption: boolean;
  complianceFrameworks: string[];
}

// Document upload result with tri-indexing info
export interface IngestResult {
  success: boolean;
  filename: string;
  chunksProcessed: number;
  message: string;
  sessionId?: string;
  documentId?: string;
  // New classification fields
  classification?: ClassificationResult;
  routingClass?: DataClass;
}

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8082';
const API_VERSION = '/api/v1';

const toSource = (s: any): IngestSource => ({
  id: s.id,
  name: s.name,
  kind: s.kind as IngestKind,
  status: (s.status as IngestStatus) ?? 'healthy',
  lastRun: s.last_run ?? '—',
  docs: Number(s.docs ?? 0),
  tags: Array.isArray(s.tags) ? s.tags : [],
  errorMessage: s.error_message || s.last_error,
  sensitivityLevel: s.sensitivity_level,
  dataCategories: s.data_categories,
  routingClass: s.routing_class,
});

const toQueueItem = (q: any): IngestQueueItem => ({
  id: q.id,
  name: q.name,
  summary: q.summary ?? '',
  status: q.status ?? 'running',
  etaLabel: q.eta_label ?? '—',
  dataClass: q.data_class,
  sensitivityLevel: q.sensitivity_level,
});

const toConnectorMetadata = (c: any): ConnectorMetadata => ({
  id: c.id,
  name: c.name,
  description: c.description,
  category: c.category,
  icon: c.icon,
  defaultClass: c.default_class,
  supportedExtensions: c.supported_extensions ?? [],
  requiresOauth: c.requires_oauth ?? false,
  requiresApiKey: c.requires_api_key ?? false,
  status: c.status ?? 'pending',
  docs: c.docs ?? 0,
});

export async function listSources(): Promise<IngestSource[]> {
  try {
    const res = await fetch(`${API_BASE}${API_VERSION}/etl/sources`);
    if (!res.ok) throw new Error('Failed to list sources');
    const data = await res.json();
    return Array.isArray(data.sources) ? data.sources.map(toSource) : [];
  } catch (err) {
    console.warn('listSources fallback (empty):', err);
    return [];
  }
}

export async function listConnectorTypes(): Promise<ConnectorMetadata[]> {
  try {
    const res = await fetch(`${API_BASE}${API_VERSION}/etl/connectors`);
    if (!res.ok) throw new Error('Failed to list connectors');
    const data = await res.json();
    return Array.isArray(data.connectors) ? data.connectors.map(toConnectorMetadata) : [];
  } catch (err) {
    console.warn('listConnectorTypes fallback:', err);
    // Return static list for UI rendering
    return getStaticConnectorList();
  }
}

export async function createSource(payload: CreateSourcePayload): Promise<IngestSource> {
  const res = await fetch(`${API_BASE}${API_VERSION}/etl/sources`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to create source');
  const data = await res.json();
  return toSource(data);
}

export async function listIngestQueue(): Promise<IngestQueueItem[]> {
  try {
    const res = await fetch(`${API_BASE}${API_VERSION}/etl/queue`);
    if (!res.ok) throw new Error('Failed to list queue');
    const data = await res.json();
    return Array.isArray(data.items) ? data.items.map(toQueueItem) : [];
  } catch (err) {
    console.warn('listIngestQueue fallback (empty):', err);
    return [];
  }
}

export async function classifyDocument(filename: string): Promise<ClassificationResult> {
  try {
    const res = await fetch(`${API_BASE}${API_VERSION}/etl/classify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename }),
    });
    if (!res.ok) throw new Error('Failed to classify');
    return await res.json();
  } catch (err) {
    console.warn('classifyDocument fallback:', err);
    return {
      sensitivityLevel: 'low',
      dataCategories: ['internal'],
      confidence: 0.5,
      decayRate: 0.8,
      requiresEncryption: false,
      complianceFrameworks: [],
    };
  }
}

export async function uploadDocument(file: File): Promise<IngestResult> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}${API_VERSION}/etl/ingest`, {
    method: 'POST',
    body: formData,
    credentials: 'include',
  });

  if (!res.ok) {
    const error = await res.text();
    throw new Error(`Upload failed: ${error}`);
  }

  const data = await res.json();
  return {
    success: data.success,
    filename: data.filename,
    chunksProcessed: data.chunks_processed,
    message: data.message,
    sessionId: data.session_id,
    documentId: data.document_id,
    classification: data.classification,
    routingClass: data.routing_class,
  };
}

// Static connector list for UI rendering when API unavailable
function getStaticConnectorList(): ConnectorMetadata[] {
  return [
    // Cloud Storage
    { id: 's3', name: 'AWS S3', description: 'Poll S3 buckets for documents', category: 'cloud_storage', icon: '🪣', defaultClass: 'CLASS_A_TRUTH', supportedExtensions: ['.pdf', '.docx', '.xlsx'], requiresOauth: false, requiresApiKey: true, status: 'pending', docs: 0 },
    { id: 'azure_blob', name: 'Azure Blob', description: 'Sync from Azure containers', category: 'cloud_storage', icon: '☁️', defaultClass: 'CLASS_A_TRUTH', supportedExtensions: ['.pdf', '.docx', '.xlsx'], requiresOauth: false, requiresApiKey: true, status: 'pending', docs: 0 },
    { id: 'gcs', name: 'Google Cloud Storage', description: 'Sync from GCS buckets', category: 'cloud_storage', icon: '🌩️', defaultClass: 'CLASS_A_TRUTH', supportedExtensions: ['.pdf', '.docx', '.xlsx'], requiresOauth: false, requiresApiKey: true, status: 'pending', docs: 0 },
    // Collaboration
    { id: 'sharepoint', name: 'SharePoint', description: 'Sync document libraries', category: 'collaboration', icon: '📂', defaultClass: 'CLASS_B_CHATTER', supportedExtensions: ['.docx', '.xlsx', '.pptx'], requiresOauth: true, requiresApiKey: false, status: 'pending', docs: 0 },
    { id: 'gdrive', name: 'Google Drive', description: 'Watch Drive folders', category: 'collaboration', icon: '📁', defaultClass: 'CLASS_B_CHATTER', supportedExtensions: ['.docx', '.xlsx', '.pptx'], requiresOauth: true, requiresApiKey: false, status: 'pending', docs: 0 },
    { id: 'onedrive', name: 'OneDrive', description: 'Sync personal or business', category: 'collaboration', icon: '☁️', defaultClass: 'CLASS_B_CHATTER', supportedExtensions: ['.docx', '.xlsx', '.pptx'], requiresOauth: true, requiresApiKey: false, status: 'pending', docs: 0 },
    { id: 'confluence', name: 'Confluence', description: 'Crawl spaces and pages', category: 'collaboration', icon: '📄', defaultClass: 'CLASS_B_CHATTER', supportedExtensions: ['.html'], requiresOauth: false, requiresApiKey: true, status: 'pending', docs: 0 },
    // Ticketing
    { id: 'servicenow', name: 'ServiceNow', description: 'Sync incidents and KB', category: 'ticketing', icon: '🎫', defaultClass: 'CLASS_C_OPS', supportedExtensions: ['.json'], requiresOauth: false, requiresApiKey: true, status: 'pending', docs: 0 },
    { id: 'jira', name: 'Jira', description: 'Sync issues and epics', category: 'ticketing', icon: '🔷', defaultClass: 'CLASS_C_OPS', supportedExtensions: ['.json'], requiresOauth: false, requiresApiKey: true, status: 'pending', docs: 0 },
    { id: 'github', name: 'GitHub', description: 'Sync issues and PRs', category: 'ticketing', icon: '🐙', defaultClass: 'CLASS_C_OPS', supportedExtensions: ['.json', '.md'], requiresOauth: false, requiresApiKey: true, status: 'pending', docs: 0 },
    // Messaging
    { id: 'slack', name: 'Slack', description: 'Archive channels', category: 'messaging', icon: '💬', defaultClass: 'CLASS_B_CHATTER', supportedExtensions: ['.json'], requiresOauth: true, requiresApiKey: false, status: 'pending', docs: 0 },
    { id: 'teams', name: 'Microsoft Teams', description: 'Archive chat history', category: 'messaging', icon: '🟦', defaultClass: 'CLASS_B_CHATTER', supportedExtensions: ['.json'], requiresOauth: true, requiresApiKey: false, status: 'pending', docs: 0 },
    { id: 'email', name: 'Email', description: 'EML/MSG/MBOX import', category: 'messaging', icon: '📧', defaultClass: 'CLASS_B_CHATTER', supportedExtensions: ['.eml', '.msg', '.mbox'], requiresOauth: false, requiresApiKey: false, status: 'healthy', docs: 0 },
    // Database
    { id: 'database', name: 'Database', description: 'SQL or NoSQL queries', category: 'database', icon: '🗄️', defaultClass: 'CLASS_C_OPS', supportedExtensions: ['.json', '.csv'], requiresOauth: false, requiresApiKey: true, status: 'pending', docs: 0 },
    { id: 'webhook', name: 'Webhook', description: 'Real-time data push', category: 'database', icon: '🔗', defaultClass: 'CLASS_C_OPS', supportedExtensions: ['.json'], requiresOauth: false, requiresApiKey: true, status: 'pending', docs: 0 },
    // Local
    { id: 'local', name: 'Local Upload', description: 'Upload from computer', category: 'local', icon: '📤', defaultClass: 'CLASS_B_CHATTER', supportedExtensions: ['.pdf', '.docx', '.xlsx', '.pptx', '.txt', '.csv', '.json'], requiresOauth: false, requiresApiKey: false, status: 'healthy', docs: 0 },
  ];
}
