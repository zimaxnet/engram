import { useEffect, useMemo, useState } from 'react'
import './GoldenThreadRunner.css'
import {
  getLatestGoldenRun,
  listGoldenDatasets,
  runGoldenThread,
  type GoldenDataset,
  type GoldenDatasetId,
  type GoldenRun,
} from '../../services/validation'

export function GoldenThreadRunner() {
  const [datasets, setDatasets] = useState<GoldenDataset[]>([])
  const [datasetId, setDatasetId] = useState<GoldenDatasetId>('cogai-thread')
  const [mode, setMode] = useState<'deterministic' | 'acceptance'>('deterministic')
  const [run, setRun] = useState<GoldenRun | null>(null)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      const [ds, last] = await Promise.all([listGoldenDatasets(), getLatestGoldenRun()])
      setDatasets(ds)
      if (last) {
        setRun(last)
        setDatasetId(last.summary.datasetId)
      }
    }

    void load()
  }, [])

  const selected = useMemo(
    () => datasets.find((d) => d.id === datasetId) ?? null,
    [datasets, datasetId]
  )

  const onRun = async () => {
    setError(null)
    setRunning(true)
    try {
      const next = await runGoldenThread({
        datasetId,
        mode,
      })
      setRun(next)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to run suite')
    } finally {
      setRunning(false)
    }
  }

  const statusPill = run?.summary.status ?? '—'

  return (
    <div className="column column-center">
      <div className="gtr page-pad">
        <div className="gtr__header">
          <div>
            <p className="eyebrow">Validation</p>
            <h2>Golden Thread</h2>
            <p className="lede">
              Run the canonical end-to-end proof suite. Produces evidence bundles, trace/workflow IDs, and Marcus/Elena narratives.
            </p>
          </div>
          <div className="gtr__header-right">
            <span className={`pill ${run?.summary.status === 'PASS' ? 'good' : run?.summary.status === 'FAIL' ? 'bad' : 'muted'}`}>
              {statusPill}
            </span>
          </div>
        </div>

        {error && (
          <div className="callout status-error" role="alert">
            {error}
          </div>
        )}

        <div className="panel">
          <div className="panel-head">
            <div>
              <p className="eyebrow">Run configuration</p>
              <h4>Choose dataset and mode</h4>
            </div>
            <div className="gtr__actions">
              <button className="primary" onClick={onRun} disabled={running}>
                {running ? 'Running…' : 'Run suite'}
              </button>
              <button className="ghost" disabled>
                Re-run failed
              </button>
            </div>
          </div>

          <div className="gtr__controls">
            <label>
              Dataset
              <select value={datasetId} onChange={(e) => setDatasetId(e.target.value as GoldenDatasetId)}>
                {datasets.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Mode
              <select value={mode} onChange={(e) => setMode(e.target.value as 'deterministic' | 'acceptance')}>
                <option value="deterministic">Deterministic (Mock Brain)</option>
                <option value="acceptance">Acceptance (Real Model)</option>
              </select>
            </label>

            <div className="gtr__dataset-meta">
              <div className="kv">
                <span className="k">File</span>
                <span className="v">{selected?.filename ?? '—'}</span>
              </div>
              <div className="kv">
                <span className="k">Hash</span>
                <span className="v mono">{selected?.hash ?? '—'}</span>
              </div>
              <div className="kv">
                <span className="k">Size</span>
                <span className="v">{selected?.sizeLabel ?? '—'}</span>
              </div>
              <div className="kv">
                <span className="k">Anchors</span>
                <span className="v">{selected?.anchors.length ?? 0}</span>
              </div>
            </div>

            {selected && (
              <div className="chip-row">
                {selected.anchors.map((a) => (
                  <span key={a} className="chip">
                    {a}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="grid-2">
          <div className="panel">
            <div className="panel-head">
              <div>
                <p className="eyebrow">Checklist</p>
                <h4>Checks</h4>
              </div>
              {run?.summary.durationMs != null && (
                <span className="pill muted">Duration: {Math.round(run.summary.durationMs / 1000)}s</span>
              )}
            </div>

            {!run && <p className="subtle">No run yet. Click “Run suite” to generate proof artifacts.</p>}

            {run && (
              <ul className="checklist">
                {run.checks.map((c) => (
                  <li key={c.id} className="check">
                    <span className={`dot ${c.status}`} aria-hidden="true" />
                    <div className="check__body">
                      <div className="check__top">
                        <strong>{c.id}</strong>
                        <span className="subtle">{c.name}</span>
                      </div>
                      <div className="check__bottom">
                        <span className="subtle">{c.evidenceSummary ?? '—'}</span>
                        {c.durationMs != null && <span className="pill muted">{c.durationMs}ms</span>}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="panel">
            <div className="panel-head">
              <div>
                <p className="eyebrow">Evidence</p>
                <h4>Traceability</h4>
              </div>
              <button
                className="ghost"
                disabled={!run}
                onClick={async () => {
                  if (!run) return
                  try {
                    const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8082'}/api/v1/validation/runs/${run.summary.runId}/evidence`, {
                      headers: {
                        'Authorization': `Bearer ${localStorage.getItem('auth_token') || ''}`,
                      },
                    })
                    const blob = await response.blob()
                    const url = window.URL.createObjectURL(blob)
                    const a = document.createElement('a')
                    a.href = url
                    a.download = `golden-thread-${run.summary.runId}.json`
                    document.body.appendChild(a)
                    a.click()
                    window.URL.revokeObjectURL(url)
                    document.body.removeChild(a)
                  } catch (error) {
                    console.error('Failed to download evidence:', error)
                    alert('Failed to download evidence bundle')
                  }
                }}
              >
                Download evidence
              </button>
            </div>

            {!run && <p className="subtle">Run the suite to produce trace IDs, workflow IDs, and an evidence bundle.</p>}

            {run && (
              <div className="evidence">
                <div className="kv">
                  <span className="k">Run ID</span>
                  <span className="v mono">{run.summary.runId}</span>
                </div>
                <div className="kv">
                  <span className="k">Trace ID</span>
                  <span className="v mono">{run.summary.traceId ?? '—'}</span>
                </div>
                <div className="kv">
                  <span className="k">Workflow ID</span>
                  <span className="v mono">{run.summary.workflowId ?? '—'}</span>
                </div>
                <div className="kv">
                  <span className="k">Session ID</span>
                  <span className="v mono">{run.summary.sessionId ?? '—'}</span>
                </div>

                <div className="narrative">
                  <div className="persona elena">
                    <strong>Elena</strong>
                    <p>{run.narrative.elena}</p>
                  </div>
                  <div className="persona marcus">
                    <strong>Marcus</strong>
                    <p>{run.narrative.marcus}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
