import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './EvidenceTelemetry.css'
import { getEvidenceTelemetry, type EvidenceTelemetrySnapshot } from '../../services/metrics'

const RANGE_OPTIONS: EvidenceTelemetrySnapshot['rangeLabel'][] = ['15m', '1h', '24h', '7d']

function statusClass(status: 'ok' | 'warn' | 'bad') {
  if (status === 'ok') return 'good'
  if (status === 'warn') return 'warn'
  return 'bad'
}

export function EvidenceTelemetry() {
  const navigate = useNavigate()
  const [range, setRange] = useState<EvidenceTelemetrySnapshot['rangeLabel']>('15m')
  const [snapshot, setSnapshot] = useState<EvidenceTelemetrySnapshot | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const data = await getEvidenceTelemetry(range)
        setSnapshot(data)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load telemetry')
      } finally {
        setLoading(false)
      }
    }

    void load()
  }, [range])

  return (
    <div className="column column-center">
      <div className="ev page-pad">
        <div className="ev__header">
          <div>
            <p className="eyebrow">Evidence</p>
            <h2>Evidence & Telemetry</h2>
            <p className="lede">
              Live operational signals + validation narratives. This is the “operator truth” layer for enterprise trust.
            </p>
          </div>
          <div className="ev__controls">
            <label className="ev__range">
              <span className="subtle">Range</span>
              <select value={range} onChange={(e) => setRange(e.target.value as EvidenceTelemetrySnapshot['rangeLabel'])}>
                {RANGE_OPTIONS.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </label>
            <button className="primary" onClick={() => navigate('/validation/golden-thread')}>Run Golden Thread</button>
            <span className="pill good">SLO: OK</span>
          </div>
        </div>

        {error && (
          <div className="callout status-error" role="alert">
            {error}
          </div>
        )}

        {loading && <p className="subtle">Loading telemetry…</p>}

        {!loading && snapshot && (
          <div className="ev__grid">
            <div className="ev__left">
              <section className="panel">
                <div className="panel-head">
                  <h4>Reliability</h4>
                </div>
                <div className="metric-grid">
                  {snapshot.reliability.map((m) => (
                    <div key={m.label} className={`metric-card ${statusClass(m.status)}`}>
                      <div className="metric-top">
                        <span className="subtle">{m.label}</span>
                        <span className={`pill ${statusClass(m.status)}`}>{m.status.toUpperCase()}</span>
                      </div>
                      <div className="metric-value">{m.value}</div>
                      {m.note && <div className="metric-note subtle">{m.note}</div>}
                    </div>
                  ))}
                </div>
              </section>

              <section className="panel">
                <div className="panel-head">
                  <h4>Ingestion</h4>
                </div>
                <div className="metric-grid">
                  {snapshot.ingestion.map((m) => (
                    <div key={m.label} className={`metric-card ${statusClass(m.status)}`}>
                      <div className="metric-top">
                        <span className="subtle">{m.label}</span>
                        <span className={`pill ${statusClass(m.status)}`}>{m.status.toUpperCase()}</span>
                      </div>
                      <div className="metric-value">{m.value}</div>
                      {m.note && <div className="metric-note subtle">{m.note}</div>}
                    </div>
                  ))}
                </div>
              </section>

              <section className="panel">
                <div className="panel-head">
                  <h4>Memory quality</h4>
                </div>
                <div className="metric-grid">
                  {snapshot.memoryQuality.map((m) => (
                    <div key={m.label} className={`metric-card ${statusClass(m.status)}`}>
                      <div className="metric-top">
                        <span className="subtle">{m.label}</span>
                        <span className={`pill ${statusClass(m.status)}`}>{m.status.toUpperCase()}</span>
                      </div>
                      <div className="metric-value">{m.value}</div>
                      {m.note && <div className="metric-note subtle">{m.note}</div>}
                    </div>
                  ))}
                </div>
              </section>
            </div>

            <div className="ev__right">
              <section className="panel">
                <div className="panel-head">
                  <h4>Alerts</h4>
                </div>
                <ul className="alert-list">
                  {snapshot.alerts.map((a) => (
                    <li key={a.id} className="alert">
                      <span className={`sev sev-${a.severity}`}>{a.severity}</span>
                      <div className="alert-body">
                        <strong>{a.title}</strong>
                        <p className="subtle">{a.detail}</p>
                        <span className="subtle">{a.timeLabel}</span>
                      </div>
                    </li>
                  ))}
                </ul>
              </section>

              <section className="panel">
                <div className="panel-head">
                  <h4>Narrative</h4>
                </div>
                <div className="persona elena">
                  <strong>Elena</strong>
                  <p>{snapshot.narrative.elena}</p>
                </div>
                <div className="persona marcus">
                  <strong>Marcus</strong>
                  <p>{snapshot.narrative.marcus}</p>
                </div>
              </section>

              <section className="panel">
                <div className="panel-head">
                  <h4>What changed</h4>
                </div>
                <div className="changes">
                  {snapshot.changes.map((c) => (
                    <div key={c.label} className="kv">
                      <span className="k">{c.label}</span>
                      <span className="v mono">{c.value}</span>
                    </div>
                  ))}
                </div>
              </section>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
