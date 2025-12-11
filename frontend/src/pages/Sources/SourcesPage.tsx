import { useEffect, useMemo, useState } from 'react';
import './SourcesPage.css';
import {
  createSource,
  listIngestQueue,
  listSources,
  type IngestKind,
  type IngestQueueItem,
  type IngestSource,
  type IngestStatus,
} from '../../services/ingestion';

type WizardStep = 0 | 1 | 2 | 3;
type ChunkHint = 'auto' | 'tables' | 'longform';

type WizardDraft = {
  kind: IngestKind;
  name: string;
  scope: string;
  retainTables: boolean;
  chunkHint: ChunkHint;
  roles: string[];
  tags: string;
};

const STEP_TITLES = ['Choose source', 'Auth & scope', 'Parsing options', 'Access & tags'];

const parseTags = (value: string) =>
  value
    .split(',')
    .map((tag) => tag.trim())
    .filter(Boolean);

const formatError = (err: unknown) =>
  err instanceof Error ? err.message : 'Unable to load sources right now.';

export function SourcesPage() {
  const [sources, setSources] = useState<IngestSource[]>([]);
  const [queue, setQueue] = useState<IngestQueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showWizard, setShowWizard] = useState(false);
  const [step, setStep] = useState<WizardStep>(0);
  const [draft, setDraft] = useState<WizardDraft>({
    kind: 'Upload',
    name: 'New source',
    scope: '',
    retainTables: true,
    chunkHint: 'auto',
    roles: ['Analyst', 'Manager'],
    tags: 'tenant:acme, project:alpha',
  });

  useEffect(() => {
    const load = async () => {
      try {
        const [sourceData, queueItems] = await Promise.all([listSources(), listIngestQueue()]);
        setSources(sourceData);
        setQueue(queueItems);
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
      });
      setSources((prev: IngestSource[]) => [next, ...prev]);
      closeWizard();
    } catch (err) {
      setError(formatError(err));
    }
  };

  const isLoadingSources = loading && sources.length === 0;

  const hasSources = sources.length > 0;

  return (
    <div className="sources-page">
      {error && (
        <div className="callout status-error" role="alert">
          {error}
        </div>
      )}

      <div className="hero">
        <div>
          <p className="eyebrow">Context Ingestion</p>
          <h1>Beautiful, reliable intake powered by Unstructured.</h1>
          <p className="lede">
            Parse PDFs, decks, chats, and exports with layout-aware fidelity. Everything gets
            tagged for tenant and RBAC before it reaches memory or the agents.
          </p>
          <div className="hero-actions">
            <button className="primary" onClick={() => openWizard()}>Add source</button>
            <button className="ghost" onClick={() => openWizard('Upload')}>Upload a file</button>
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
              <div className="metric">≤2.4s</div>
              <div className="label">Median parse</div>
            </div>
          </div>
        </div>
        <div className="hero-card">
          <div className="pill">Unstructured API</div>
          <h3>Layout-aware parsing</h3>
          <p>
            Tables, lists, headers, and captions stay intact. PII redaction and ACL tagging can
            be enforced at ingest time.
          </p>
          <ul>
            <li>Scale-to-zero friendly</li>
            <li>HTTP/JSON interface</li>
            <li>Pushes to Zep (graph + vector)</li>
          </ul>
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
              <div className="stat-line">
                <span>Docs</span>
                <strong>{source.docs}</strong>
              </div>
              <div className="tag-row">
                {source.tags.map((tag) => (
                  <span key={tag} className="tag">{tag}</span>
                ))}
              </div>
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
          No sources connected yet. Add S3, SharePoint, Drive, or uploads to parse through Unstructured.
        </div>
      )}

      <div className="flex-row">
        <div className="panel">
          <div className="panel-head">
            <div>
              <p className="eyebrow">In-flight</p>
              <h4>Parsing queue</h4>
            </div>
            <button className="ghost sm" onClick={() => openWizard('Upload')}>New ingest</button>
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
                  <p className="subtle">Kick off a run to see live Unstructured parses.</p>
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
            <button className="ghost sm" onClick={() => openWizard('Upload')}>Use sample</button>
          </div>
          <div className="dropzone">
            <p className="drop-emoji">📤</p>
            <p className="lede">Drag & drop files or click to browse</p>
            <p className="subtle">PDF, PPTX, DOCX, HTML, EML</p>
            <button className="primary sm" onClick={() => openWizard('Upload')}>Upload</button>
          </div>
          <div className="hint">
            Parsed via Unstructured → tagged → Zep Graphiti → Agents. Median parse under 3s.
          </div>
        </div>
      </div>

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
              {step === 0 && (
                <div className="grid-2">
                  {(['Upload', 'S3', 'SharePoint', 'Drive', 'Email'] as IngestKind[]).map((kind) => (
                    <button
                      key={kind}
                      className={`select-card ${draft.kind === kind ? 'selected' : ''}`}
                      onClick={() => setDraft((prev: WizardDraft) => ({ ...prev, kind, name: `${kind} source` }))}
                    >
                      <div className="pill muted">{kind}</div>
                      <h4>{kind}</h4>
                      <p className="subtle">
                        {kind === 'Upload' && 'One-off drops for PDFs, PPTX, DOCX, HTML.'}
                        {kind === 'S3' && 'Bucket/prefix watcher with serverless polling.'}
                        {kind === 'SharePoint' && 'Site/library polling with delta sync.'}
                        {kind === 'Drive' && 'Folder watcher with incremental updates.'}
                        {kind === 'Email' && 'Ingest EML/MBOX exports with thread preservation.'}
                      </p>
                    </button>
                  ))}
                </div>
              )}

              {step === 1 && (
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
                      placeholder="tenant:acme, project:alpha, sensitivity:gold"
                    />
                  </label>
                  <div className="inline">
                    <span className="pill muted">Auth will be requested in backend</span>
                    <span className="subtle">OAuth / key / signed URL depending on kind.</span>
                  </div>
                </div>
              )}

              {step === 2 && (
                <div className="form-grid">
                  <label>
                    Parsing profile
                    <select
                      value={draft.chunkHint}
                      onChange={(e) => setDraft((prev: WizardDraft) => ({ ...prev, chunkHint: e.target.value as ChunkHint }))}
                    >
                      <option value="auto">Auto (layout-aware)</option>
                      <option value="tables">Prefer tables intact</option>
                      <option value="longform">Long-form blocks</option>
                    </select>
                  </label>
                  <label className="checkbox-row">
                    <input
                      type="checkbox"
                      checked={draft.retainTables}
                      onChange={(e) => setDraft((prev: WizardDraft) => ({ ...prev, retainTables: e.target.checked }))}
                    />
                    Preserve table structure
                  </label>
                  <div className="callout">
                    Parsed by Unstructured → tagged → sent to Zep (graph + vectors) with tenant and role filters.
                  </div>
                </div>
              )}

              {step === 3 && (
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
                    RBAC is enforced at query time; items will be tagged with tenant + roles on ingest.
                  </div>
                </div>
              )}
            </div>

            <div className="modal-footer">
              <div className="left">
                <span className="pill muted">Scale-to-zero • Pay-per-parse</span>
              </div>
              <div className="right">
                <button className="ghost" onClick={closeWizard}>Cancel</button>
                {step > 0 && (
                  <button className="ghost" onClick={() => setStep((s) => (s - 1) as WizardStep)}>
                    Back
                  </button>
                )}
                {step < 3 ? (
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
      : 'Error';
  return <span className={`pill status-${status}`}>{label}</span>;
}
