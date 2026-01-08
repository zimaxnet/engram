import { useEffect, useMemo, useState } from 'react';
import './SourcesPage.css';

import {
  createSource,
  listIngestQueue,
  listSources,
  listConnectorTypes,
  type ConnectorMetadata,
  type IngestKind,
  type IngestQueueItem,
  type IngestSource,
  type IngestStatus,
  type SensitivityLevel,
  type DataCategory,
  type DataClass,
} from '../../services/ingestion';

type WizardStep = 0 | 1 | 2 | 3 | 4;
type ChunkHint = 'auto' | 'tables' | 'longform';

type WizardDraft = {
  kind: IngestKind;
  name: string;
  scope: string;
  retainTables: boolean;
  chunkHint: ChunkHint;
  roles: string[];
  tags: string;
  sensitivityLevel: SensitivityLevel;
  dataCategories: DataCategory[];
};

const STEP_TITLES = ['Choose source', 'Classification', 'Auth & scope', 'Parsing options', 'Access & tags'];

const parseTags = (value: string) =>
  value
    .split(',')
    .map((tag) => tag.trim())
    .filter(Boolean);

const formatError = (err: unknown) =>
  err instanceof Error ? err.message : 'Unable to load sources right now.';

// Data class info for visualization
const DATA_CLASS_INFO: Record<DataClass, { name: string; engine: string; emoji: string; color: string }> = {
  CLASS_A_TRUTH: { name: 'Class A: Immutable Truth', engine: 'Docling (IBM)', emoji: '📚', color: '#ef4444' },
  CLASS_B_CHATTER: { name: 'Class B: Ephemeral Chatter', engine: 'Unstructured.io', emoji: '💬', color: '#f59e0b' },
  CLASS_C_OPS: { name: 'Class C: Operational', engine: 'Pandas', emoji: '📊', color: '#22c55e' },
};

const SENSITIVITY_INFO: Record<SensitivityLevel, { label: string; emoji: string; color: string; description: string }> = {
  high: { label: 'High Impact', emoji: '🔴', color: '#ef4444', description: 'Safety-critical, PII, credentials' },
  moderate: { label: 'Moderate Impact', emoji: '🟡', color: '#f59e0b', description: 'Business confidential, specs' },
  low: { label: 'Low Impact', emoji: '🟢', color: '#22c55e', description: 'General communications' },
};

const CATEGORY_LABELS: Record<DataCategory, string> = {
  pii: 'PII',
  phi: 'PHI (HIPAA)',
  cui: 'CUI',
  pci: 'PCI-DSS',
  proprietary: 'Proprietary',
  safety: 'Safety-Critical',
  credential: 'Credentials',
  public: 'Public',
  internal: 'Internal',
};

const CONNECTOR_CATEGORIES = [
  { id: 'cloud_storage', name: 'Cloud Storage', emoji: '☁️' },
  { id: 'collaboration', name: 'Collaboration', emoji: '📁' },
  { id: 'ticketing', name: 'Ticketing', emoji: '🎫' },
  { id: 'messaging', name: 'Messaging', emoji: '💬' },
  { id: 'database', name: 'Database', emoji: '🗄️' },
  { id: 'local', name: 'Local', emoji: '📤' },
];

export function SourcesPage() {
  const [sources, setSources] = useState<IngestSource[]>([]);
  const [queue, setQueue] = useState<IngestQueueItem[]>([]);
  const [connectors, setConnectors] = useState<ConnectorMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showWizard, setShowWizard] = useState(false);
  const [step, setStep] = useState<WizardStep>(0);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [draft, setDraft] = useState<WizardDraft>({
    kind: 'Local',
    name: 'New source',
    scope: '',
    retainTables: true,
    chunkHint: 'auto',
    roles: ['Analyst', 'Manager'],
    tags: 'tenant:acme, project:alpha',
    sensitivityLevel: 'low',
    dataCategories: ['internal'],
  });

  useEffect(() => {
    const load = async () => {
      try {
        const [sourceData, queueItems, connectorTypes] = await Promise.all([
          listSources(),
          listIngestQueue(),
          listConnectorTypes(),
        ]);
        setSources(sourceData);
        setQueue(queueItems);
        setConnectors(connectorTypes);
      } catch (err) {
        setError(formatError(err));
      } finally {
        setLoading(false);
      }
    };

    void load();
  }, []);

  const healthyCount = useMemo(
    () => sources.filter((source: IngestSource) => source.status === 'healthy').length,
    [sources]
  );

  const openWizard = (kind?: IngestKind) => {
    setDraft((prev: WizardDraft) => ({
      ...prev,
      kind: kind ?? prev.kind,
      name: prev.name || `${kind ?? prev.kind} source`,
    }));
    setShowWizard(true);
    setStep(0);
  };

  const closeWizard = () => {
    setShowWizard(false);
    setStep(0);
  };

  const handleSave = async () => {
    try {
      const next = await createSource({
        name: draft.name || 'New source',
        kind: draft.kind,
        scope: draft.scope,
        tags: parseTags(draft.tags),
        retainTables: draft.retainTables,
        chunkHint: draft.chunkHint,
        roles: draft.roles,
        sensitivityLevel: draft.sensitivityLevel,
        dataCategories: draft.dataCategories,
      });
      setSources((prev: IngestSource[]) => [next, ...prev]);
      closeWizard();
    } catch (err) {
      setError(formatError(err));
    }
  };

  const isLoadingSources = loading && sources.length === 0;
  const hasSources = sources.length > 0;

  const groupedConnectors = useMemo(() => {
    const groups: Record<string, ConnectorMetadata[]> = {};
    for (const cat of CONNECTOR_CATEGORIES) {
      groups[cat.id] = connectors.filter(c => c.category === cat.id);
    }
    return groups;
  }, [connectors]);

  return (
    <div className="column column-center sources-page">
      {error && (
        <div className="callout status-error" role="alert">
          {error}
        </div>
      )}

      {/* HERO: Antigravity Router Visualization */}
      <div className="hero">
        <div>
          <p className="eyebrow">Antigravity Context Ingestion</p>
          <h1>Enterprise-grade intake with intelligent routing.</h1>
          <p className="lede">
            Documents are classified by Truth Value and routed to specialized engines.
            NIST SP 800-60 aligned classification ensures compliance.
          </p>
          <div className="hero-actions">
            <button className="primary" onClick={() => openWizard()}>Add source</button>
            <button className="ghost" onClick={() => openWizard('Local')}>Upload a file</button>
          </div>
          <div className="hero-metrics">
            <div>
              <div className="metric">{isLoadingSources ? '…' : sources.length}</div>
              <div className="label">Sources connected</div>
            </div>
            <div>
              <div className="metric">{isLoadingSources ? '…' : healthyCount}</div>
              <div className="label">Healthy</div>
            </div>
            <div>
              <div className="metric">16</div>
              <div className="label">Connector types</div>
            </div>
          </div>
        </div>

        {/* Router Flow Visualization */}
        <div className="router-card">
          <div className="pill">Antigravity Router</div>
          <h3>Intelligent Document Routing</h3>
          <div className="router-flow">
            {Object.entries(DATA_CLASS_INFO).map(([key, info]) => (
              <div key={key} className={`router-class router-class-${key.toLowerCase()}`}>
                <span className="class-emoji">{info.emoji}</span>
                <div>
                  <strong>{info.name.split(':')[1]}</strong>
                  <span className="engine-label">{info.engine}</span>
                </div>
              </div>
            ))}
          </div>
          <div className="nist-badge">
            <span>🛡️</span>
            <span>NIST SP 800-60 • FIPS 199</span>
          </div>
        </div>
      </div>

      {/* Data Classification Legend */}
      <div className="classification-panel">
        <div className="panel-head">
          <div>
            <p className="eyebrow">Data Classification</p>
            <h4>NIST AI RMF Impact Levels</h4>
          </div>
        </div>
        <div className="sensitivity-grid">
          {Object.entries(SENSITIVITY_INFO).map(([level, info]) => (
            <div key={level} className={`sensitivity-card sensitivity-${level}`}>
              <div className="sensitivity-header">
                <span>{info.emoji}</span>
                <strong>{info.label}</strong>
              </div>
              <p className="subtle">{info.description}</p>
            </div>
          ))}
        </div>
      </div>

      {isLoadingSources && <p className="subtle">Loading sources…</p>}

      {!isLoadingSources && hasSources && (
        <div className="sources-grid">
          {sources.map((source) => (
            <div key={source.id} className="source-card">
              <div className="source-card__top">
                <div className="pill muted">{source.kind}</div>
                <StatusChip status={source.status} />
              </div>
              <h3>{source.name}</h3>
              <p className="subtle">Last run: {source.lastRun}</p>
              {source.sensitivityLevel && (
                <div className="classification-badge" data-level={source.sensitivityLevel}>
                  {SENSITIVITY_INFO[source.sensitivityLevel].emoji} {SENSITIVITY_INFO[source.sensitivityLevel].label}
                </div>
              )}
              <div className="stat-line">
                <span>Docs</span>
                <strong>{source.docs}</strong>
              </div>
              <div className="tag-row">
                {source.tags.map((tag) => (
                  <span key={tag} className="tag">{tag}</span>
                ))}
              </div>
              {source.status === 'error' && source.errorMessage && (
                <div className="error-details">
                  <span className="error-icon">⚠️</span>
                  {source.errorMessage}
                </div>
              )}
              <div className="card-actions">
                <button className="ghost sm">View activity</button>
                <button className="ghost sm">Pause</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {!isLoadingSources && !hasSources && (
        <div className="callout">
          No sources connected yet. Choose from 16 connector types below to start ingesting documents.
        </div>
      )}

      {/* Connector Library */}
      <div className="connector-library">
        <div className="panel-head">
          <div>
            <p className="eyebrow">Connector Library</p>
            <h4>All Enterprise Data Sources</h4>
          </div>
        </div>
        <div className="category-tabs">
          {CONNECTOR_CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              className={`category-tab ${activeCategory === cat.id ? 'active' : ''}`}
              onClick={() => setActiveCategory(activeCategory === cat.id ? null : cat.id)}
            >
              <span>{cat.emoji}</span>
              <span>{cat.name}</span>
              <span className="count">{groupedConnectors[cat.id]?.length || 0}</span>
            </button>
          ))}
        </div>
        <div className="connector-grid">
          {connectors
            .filter(c => !activeCategory || c.category === activeCategory)
            .map((connector) => (
              <button
                key={connector.id}
                className="connector-card"
                onClick={() => openWizard(connector.id.charAt(0).toUpperCase() + connector.id.slice(1) as IngestKind)}
              >
                <div className="connector-icon">{connector.icon}</div>
                <div className="connector-info">
                  <strong>{connector.name}</strong>
                  <p className="subtle">{connector.description}</p>
                </div>
                <div className="connector-meta">
                  <span className={`pill ${connector.status === 'healthy' ? 'good' : 'muted'}`}>
                    {connector.status}
                  </span>
                  {connector.requiresOauth && <span className="pill muted">OAuth</span>}
                </div>
              </button>
            ))}
        </div>
      </div>

      {/* Queue Panel */}
      <div className="flex-row">
        <div className="panel">
          <div className="panel-head">
            <div>
              <p className="eyebrow">In-flight</p>
              <h4>Parsing queue</h4>
            </div>
            <button className="ghost sm" onClick={() => openWizard('Local')}>New ingest</button>
          </div>
          <ul className="timeline">
            {queue.map((item) => (
              <li key={item.id}>
                <div className={`dot ${item.status === 'running' ? 'running' : item.status === 'paused' ? 'paused' : ''}`} />
                <div>
                  <strong>{item.name}</strong>
                  <p className="subtle">{item.summary}</p>
                </div>
                <span className={`pill ${item.status === 'completed' ? 'good' : 'muted'}`}>
                  {item.etaLabel}
                </span>
              </li>
            ))}
            {!loading && queue.length === 0 && (
              <li>
                <div className="dot" />
                <div>
                  <strong>No queued ingests</strong>
                  <p className="subtle">Kick off a run to see live parses.</p>
                </div>
                <span className="pill muted">idle</span>
              </li>
            )}
          </ul>
        </div>

        <div className="panel upload-panel">
          <div className="panel-head">
            <div>
              <p className="eyebrow">Quick ingest</p>
              <h4>Drop a document</h4>
            </div>
            <button className="ghost sm" onClick={() => openWizard('Local')}>Use sample</button>
          </div>
          <div className="dropzone">
            <p className="drop-emoji">📤</p>
            <p className="lede">Drag & drop files or click to browse</p>
            <p className="subtle">PDF, PPTX, DOCX, HTML, EML, CSV, JSON</p>
            <button className="primary sm" onClick={() => openWizard('Local')}>Upload</button>
          </div>
          <div className="hint">
            Routed via Antigravity → classified → indexed → Agents. NIST-aligned metadata.
          </div>
        </div>
      </div>

      {/* Wizard Modal */}
      {showWizard && (
        <div className="modal-backdrop" onClick={closeWizard}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <p className="eyebrow">Add source</p>
                <h3>{STEP_TITLES[step]}</h3>
              </div>
              <button className="ghost" onClick={closeWizard}>✕</button>
            </div>

            <div className="steps">
              {STEP_TITLES.map((title, idx) => {
                const active = idx === step;
                return (
                  <div key={title} className={`step ${active ? 'active' : ''}`}>
                    <div className="step-index">{idx + 1}</div>
                    <div className="step-label">{title}</div>
                  </div>
                );
              })}
            </div>

            <div className="modal-body">
              {/* Step 0: Choose Source */}
              {step === 0 && (
                <div className="grid-3">
                  {connectors.slice(0, 9).map((connector) => (
                    <button
                      key={connector.id}
                      className={`select-card ${draft.kind === connector.name ? 'selected' : ''}`}
                      onClick={() => setDraft((prev: WizardDraft) => ({ ...prev, kind: connector.name as IngestKind, name: `${connector.name} source` }))}
                    >
                      <span className="connector-icon-lg">{connector.icon}</span>
                      <h4>{connector.name}</h4>
                      <p className="subtle">{connector.description}</p>
                    </button>
                  ))}
                </div>
              )}

              {/* Step 1: Classification (NEW) */}
              {step === 1 && (
                <div className="form-grid">
                  <label>
                    <strong>Sensitivity Level (NIST SP 800-60)</strong>
                    <div className="sensitivity-selector">
                      {Object.entries(SENSITIVITY_INFO).map(([level, info]) => (
                        <button
                          key={level}
                          className={`sensitivity-option ${draft.sensitivityLevel === level ? 'selected' : ''}`}
                          onClick={() => setDraft((prev: WizardDraft) => ({ ...prev, sensitivityLevel: level as SensitivityLevel }))}
                          data-selected={draft.sensitivityLevel === level}
                        >
                          <span>{info.emoji}</span>
                          <span>{info.label}</span>
                        </button>
                      ))}
                    </div>
                  </label>
                  <label>
                    <strong>Data Categories</strong>
                    <div className="category-checkboxes">
                      {Object.entries(CATEGORY_LABELS).map(([cat, label]) => (
                        <label key={cat} className="checkbox-row">
                          <input
                            type="checkbox"
                            checked={draft.dataCategories.includes(cat as DataCategory)}
                            onChange={(e) => {
                              setDraft((prev: WizardDraft) => ({
                                ...prev,
                                dataCategories: e.target.checked
                                  ? [...prev.dataCategories, cat as DataCategory]
                                  : prev.dataCategories.filter(c => c !== cat)
                              }));
                            }}
                          />
                          {label}
                        </label>
                      ))}
                    </div>
                  </label>
                  <div className="callout">
                    <strong>🛡️ Compliance Frameworks:</strong> Classification determines retention, encryption, and audit requirements.
                  </div>
                </div>
              )}

              {/* Step 2: Auth & Scope */}
              {step === 2 && (
                <div className="form-grid">
                  <label>
                    Source name
                    <input
                      value={draft.name}
                      onChange={(e) => setDraft((prev: WizardDraft) => ({ ...prev, name: e.target.value }))}
                      placeholder="e.g., S3 - finance-reports"
                    />
                  </label>
                  <label>
                    Scope / path
                    <input
                      value={draft.scope}
                      onChange={(e) => setDraft((prev: WizardDraft) => ({ ...prev, scope: e.target.value }))}
                      placeholder="s3://bucket/prefix or site/library"
                    />
                  </label>
                  <label>
                    Tags
                    <input
                      value={draft.tags}
                      onChange={(e) => setDraft((prev: WizardDraft) => ({ ...prev, tags: e.target.value }))}
                      placeholder="tenant:acme, project:alpha, sensitivity:high"
                    />
                  </label>
                  <div className="inline">
                    <span className="pill muted">Auth will be requested in backend</span>
                    <span className="subtle">OAuth / key / signed URL depending on kind.</span>
                  </div>
                </div>
              )}

              {/* Step 3: Parsing Options */}
              {step === 3 && (
                <div className="form-grid">
                  <label>
                    Parsing profile
                    <select
                      value={draft.chunkHint}
                      onChange={(e) => setDraft((prev: WizardDraft) => ({ ...prev, chunkHint: e.target.value as ChunkHint }))}
                    >
                      <option value="auto">Auto (Antigravity Router)</option>
                      <option value="tables">Prefer tables intact (Docling)</option>
                      <option value="longform">Long-form blocks (Unstructured)</option>
                    </select>
                  </label>
                  <label className="checkbox-row">
                    <input
                      type="checkbox"
                      checked={draft.retainTables}
                      onChange={(e) => setDraft((prev: WizardDraft) => ({ ...prev, retainTables: e.target.checked }))}
                    />
                    Preserve table structure (TableFormer)
                  </label>
                  <div className="callout">
                    Antigravity routes: PDF/Specs → Docling | Email/PPT → Unstructured | CSV/JSON → Pandas
                  </div>
                </div>
              )}

              {/* Step 4: Access & Tags */}
              {step === 4 && (
                <div className="form-grid">
                  <label>
                    Roles with access
                    <input
                      value={draft.roles.join(', ')}
                      onChange={(e) => setDraft((prev: WizardDraft) => ({ ...prev, roles: e.target.value.split(',').map((role: string) => role.trim()) }))}
                      placeholder="Analyst, Manager"
                    />
                  </label>
                  <div className="hint">
                    RBAC is enforced at query time; items tagged with tenant + roles + sensitivity level.
                  </div>
                </div>
              )}
            </div>

            <div className="modal-footer">
              <div className="left">
                <span className="pill muted">Antigravity • NIST Aligned</span>
              </div>
              <div className="right">
                <button className="ghost" onClick={closeWizard}>Cancel</button>
                {step > 0 && (
                  <button className="ghost" onClick={() => setStep((s) => (s - 1) as WizardStep)}>
                    Back
                  </button>
                )}
                {step < 4 ? (
                  <button className="primary" onClick={() => setStep((s) => (s + 1) as WizardStep)}>
                    Next
                  </button>
                ) : (
                  <button className="primary" onClick={handleSave}>
                    Create & queue
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatusChip({ status }: { status: IngestStatus }) {
  const label =
    status === 'healthy'
      ? 'Healthy'
      : status === 'indexing'
        ? 'Indexing'
        : status === 'paused'
          ? 'Paused'
          : status === 'pending'
            ? 'Pending'
            : 'Error';
  return <span className={`pill status-${status}`}>{label}</span>;
}
