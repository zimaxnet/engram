import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import './WorkflowDetail.css'

/* Inline styles for step IO */
const stepIoStyle = `
  .step-io {
    margin-top: 8px;
    font-size: 0.75rem;
  }
  .step-io summary {
    cursor: pointer;
    color: var(--color-text-muted);
    font-family: var(--font-mono);
  }
  .step-io-content {
    margin-top: 4px;
    padding: 8px;
    background: rgba(0,0,0,0.2);
    border-radius: 4px;
  }
  .step-io pre {
    margin: 4px 0 8px 0;
    white-space: pre-wrap;
    word-break: break-all;
    font-family: var(--font-mono);
    color: var(--color-text-dim);
  }
  .step-io label {
    display: block;
    font-weight: 600;
    color: var(--color-text-muted);
    margin-bottom: 2px;
  }
`;

import { getWorkflowDetail, type WorkflowDetailModel } from '../../services/workflowDetail'
import { signalWorkflow } from '../../services/api'
import { AGENTS, type AgentId } from '../../types'

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
      <style>{stepIoStyle}</style>
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
                  <h4>{detail.workflowType === 'StoryWorkflow' ? 'Story & Visual Creation' : detail.workflowType}</h4>
                  <p className="subtle mono">{detail.workflowId}</p>
                </div>
                <div className="wfd__badges">
                  <span className="pill good">{detail.status.toUpperCase()}</span>
                  {detail.workflowType === 'StoryWorkflow' && (
                    <>
                      <span className="pill muted" style={{ background: AGENTS.elena.accentColor + '20', color: AGENTS.elena.accentColor }}>
                        Elena → Sage
                      </span>
                      <span className="pill muted">Delegation</span>
                    </>
                  )}
                  {detail.agentId && <span className="pill muted">Agent: {detail.agentId}</span>}
                  {detail.sessionId && <span className="pill muted mono">Session: {detail.sessionId}</span>}
                </div>
              </div>
              
              {/* Story Workflow Progress Bar */}
              {detail.workflowType === 'StoryWorkflow' && detail.steps.length > 0 && (
                <div style={{
                  margin: '1rem 0',
                  padding: '1rem',
                  background: 'rgba(255,255,255,0.03)',
                  borderRadius: '8px',
                  border: '1px solid var(--glass-border)'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <span style={{ fontSize: '0.9em', opacity: 0.8 }}>Progress</span>
                    <span style={{ fontSize: '0.9em', opacity: 0.8 }}>
                      {Math.round((detail.steps.filter(s => s.status === 'completed').length / detail.steps.length) * 100)}%
                    </span>
                  </div>
                  <div style={{
                    width: '100%',
                    height: '8px',
                    background: 'rgba(255,255,255,0.1)',
                    borderRadius: '4px',
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      width: `${(detail.steps.filter(s => s.status === 'completed').length / detail.steps.length) * 100}%`,
                      height: '100%',
                      background: 'linear-gradient(90deg, var(--color-primary), var(--color-accent-cyan))',
                      transition: 'width 0.3s ease'
                    }}></div>
                  </div>
                </div>
              )}

              <div className="timeline">
                {detail.steps.map((s) => {
                  // Format step names for story workflows
                  const stepName = detail.workflowType === 'StoryWorkflow' 
                    ? s.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
                    : s.name;
                  
                  return (
                    <div key={s.name} className="step">
                      <span className={`dot ${s.status}`} />
                      <div className="step-body">
                        <div className="step-top">
                          <strong className="mono">{stepName}</strong>
                          <span className="pill muted">{s.status}</span>
                        </div>
                        <div className="step-bottom">
                          <span className="subtle">{s.meta ?? ''}</span>
                          <span className="subtle">
                            {s.durationLabel ?? '—'} {s.attempts != null ? `• attempts: ${s.attempts}` : ''}
                          </span>
                        </div>
                        {s.note && <div className="callout">{s.note}</div>}
                        {(!!s.inputs || !!s.outputs) && (
                          <div className="step-io">
                            <details>
                              <summary>IO Trace</summary>
                              <div className="step-io-content">
                                {!!s.inputs && (
                                  <div>
                                    <label>Inputs</label>
                                    <pre>{JSON.stringify(s.inputs, null, 2)}</pre>
                                  </div>
                                )}
                                {!!s.outputs && (
                                  <div>
                                    <label>Outputs</label>
                                    <pre>{JSON.stringify(s.outputs, null, 2)}</pre>
                                  </div>
                                )}
                              </div>
                            </details>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>

            <aside className="panel">
              {/* Story Preview for Story Workflows */}
              {detail.workflowType === 'StoryWorkflow' && detail.contextSnapshot?.find(kv => kv.k === 'preview') && (
                <>
                  <div className="panel-head">
                    <h4>Story Preview</h4>
                  </div>
                  <div style={{
                    padding: '1rem',
                    background: 'rgba(255,255,255,0.03)',
                    borderRadius: '6px',
                    marginBottom: '1rem',
                    border: '1px solid var(--glass-border)',
                    maxHeight: '200px',
                    overflowY: 'auto',
                    fontSize: '0.9em',
                    lineHeight: '1.6',
                    whiteSpace: 'pre-wrap'
                  }}>
                    {detail.contextSnapshot.find(kv => kv.k === 'preview')?.v || 'No preview available'}
                  </div>
                </>
              )}
              
              <div className="panel-head">
                <h4>Context snapshot (redacted)</h4>
              </div>
              <div className="kv-list">
                {detail.contextSnapshot.filter(kv => kv.k !== 'preview').map((kv) => (
                  <div key={kv.k} className="kv">
                    <span className="k">{kv.k}</span>
                    <span className="v">{kv.v}</span>
                  </div>
                ))}
                {detail.contextSnapshot.length === 0 && (
                  <div className="subtle" style={{ padding: '1rem', textAlign: 'center' }}>
                    No context snapshot available
                  </div>
                )}
              </div>
              <div className="callout">Sensitive fields are redacted. Signals are audited and tenant-scoped.</div>
              
              {/* Delegation Info for Story Workflows */}
              {detail.workflowType === 'StoryWorkflow' && (
                <>
                  <div className="panel-head" style={{ marginTop: '1rem' }}>
                    <h4>Delegation Chain</h4>
                  </div>
                  <div style={{
                    padding: '1rem',
                    background: 'rgba(255,255,255,0.03)',
                    borderRadius: '6px',
                    marginBottom: '1rem',
                    border: '1px solid var(--glass-border)'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                      <div style={{
                        width: '32px',
                        height: '32px',
                        borderRadius: '50%',
                        background: AGENTS.elena.accentColor,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#fff',
                        fontWeight: 'bold',
                        fontSize: '0.9em'
                      }}>
                        E
                      </div>
                      <span style={{ fontSize: '0.9em' }}>Elena (delegator)</span>
                    </div>
                    <div style={{ 
                      marginLeft: '16px',
                      marginBottom: '0.5rem',
                      paddingLeft: '1rem',
                      borderLeft: '2px solid var(--glass-border)',
                      opacity: 0.6
                    }}>
                      <span style={{ fontSize: '0.85em' }}>↓ delegates story/visual creation</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <div style={{
                        width: '32px',
                        height: '32px',
                        borderRadius: '50%',
                        background: AGENTS.sage.accentColor,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#fff',
                        fontWeight: 'bold',
                        fontSize: '0.9em'
                      }}>
                        S
                      </div>
                      <span style={{ fontSize: '0.9em' }}>Sage (executor)</span>
                    </div>
                    <div style={{ 
                      marginTop: '0.75rem',
                      padding: '0.75rem',
                      background: 'rgba(255,255,255,0.05)',
                      borderRadius: '4px',
                      fontSize: '0.85em',
                      opacity: 0.8
                    }}>
                      <strong>Workflow Type:</strong> StoryWorkflow<br/>
                      <strong>Execution:</strong> Durable via Temporal<br/>
                      <strong>Steps:</strong> Story → Diagram → Image → Save → Memory
                    </div>
                  </div>
                </>
              )}

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
