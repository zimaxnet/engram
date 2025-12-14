import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import './WorkflowDetail.css'
import { getWorkflowDetail, type WorkflowDetailModel } from '../../services/workflowDetail'
import { signalWorkflow } from '../../services/api'

export function WorkflowDetail() {
  const { workflowId } = useParams()
  const navigate = useNavigate()
  const [detail, setDetail] = useState<WorkflowDetailModel | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [signaling, setSignaling] = useState(false)

  useEffect(() => {
    const load = async () => {
      if (!workflowId) return
      setLoading(true)
      setError(null)
      try {
        const data = await getWorkflowDetail(workflowId)
        setDetail(data)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load workflow')
      } finally {
        setLoading(false)
      }
    }
    void load()
  }, [workflowId])

  const handleSignal = async (signalName: string, payload: unknown = {}) => {
    if (!workflowId) return
    setSignaling(true)
    try {
      await signalWorkflow(workflowId, signalName, payload)
      // Reload workflow detail after signal
      const data = await getWorkflowDetail(workflowId)
      setDetail(data)
    } catch (e) {
      alert(`Failed to send signal: ${e instanceof Error ? e.message : 'Unknown error'}`)
    } finally {
      setSignaling(false)
    }
  }

  return (
    <div className="column column-center">
      <div className="wfd page-pad">
        <div className="wfd__header">
          <div>
            <p className="eyebrow">Workflows</p>
            <h2>Workflow detail</h2>
            <p className="lede">Durable execution history, retries, signals, and safe context snapshots.</p>
          </div>
        </div>

        {loading && <p className="subtle">Loading workflow…</p>}

        {error && (
          <div className="callout status-error" role="alert">
            {error}
          </div>
        )}

        {!loading && detail && (
          <div className="wfd__grid">
            <section className="panel">
              <div className="panel-head">
                <div>
                  <h4>{detail.workflowType}</h4>
                  <p className="subtle mono">{detail.workflowId}</p>
                </div>
                <div className="wfd__badges">
                  <span className="pill good">{detail.status.toUpperCase()}</span>
                  {detail.agentId && <span className="pill muted">Agent: {detail.agentId}</span>}
                  {detail.sessionId && <span className="pill muted mono">Session: {detail.sessionId}</span>}
                </div>
              </div>

              <div className="timeline">
                {detail.steps.map((s) => (
                  <div key={s.name} className="step">
                    <span className={`dot ${s.status}`} />
                    <div className="step-body">
                      <div className="step-top">
                        <strong className="mono">{s.name}</strong>
                        <span className="pill muted">{s.status}</span>
                      </div>
                      <div className="step-bottom">
                        <span className="subtle">{s.meta ?? ''}</span>
                        <span className="subtle">
                          {s.durationLabel ?? '—'} {s.attempts != null ? `• attempts: ${s.attempts}` : ''}
                        </span>
                      </div>
                      {s.note && <div className="callout">{s.note}</div>}
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <aside className="panel">
              <div className="panel-head">
                <h4>Context snapshot (redacted)</h4>
              </div>
              <div className="kv-list">
                {detail.contextSnapshot.map((kv) => (
                  <div key={kv.k} className="kv">
                    <span className="k">{kv.k}</span>
                    <span className="v">{kv.v}</span>
                  </div>
                ))}
              </div>
              <div className="callout">Sensitive fields are redacted. Signals are audited and tenant-scoped.</div>

              <div className="panel-head" style={{ marginTop: '1rem' }}>
                <h4>Signals</h4>
              </div>
              <div className="signal-row">
                <button
                  className="primary sm"
                  onClick={() => handleSignal('approve', { approved: true })}
                  disabled={signaling}
                >
                  Approve
                </button>
                <button
                  className="ghost sm"
                  onClick={() => handleSignal('provide_input', { input: prompt('Provide input:') || '' })}
                  disabled={signaling}
                >
                  Provide input
                </button>
                <button
                  className="danger sm"
                  onClick={() => handleSignal('cancel', {})}
                  disabled={signaling}
                >
                  Cancel
                </button>
              </div>

              <div className="panel-head" style={{ marginTop: '1rem' }}>
                <h4>Trace</h4>
              </div>
              <div className="kv">
                <span className="k">Trace ID</span>
                <span className="v mono">{detail.traceId ?? '—'}</span>
              </div>
              <button className="ghost sm" onClick={() => navigate('/evidence')}>Open in telemetry</button>
            </aside>
          </div>
        )}
      </div>
    </div>
  )
}
