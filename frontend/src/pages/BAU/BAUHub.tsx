import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './BAUHub.css'
import { listBauFlows, listRecentArtifacts, type BauArtifact, type BauFlow } from '../../services/bau'
import { startBauFlow } from '../../services/api'

export function BAUHub() {
  const navigate = useNavigate()
  const [flows, setFlows] = useState<BauFlow[]>([])
  const [artifacts, setArtifacts] = useState<BauArtifact[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true)
        const [f, a] = await Promise.all([listBauFlows(), listRecentArtifacts()])
        setFlows(f)
        setArtifacts(a)
      } catch (error) {
        console.error('Failed to load BAU data:', error)
      } finally {
        setLoading(false)
      }
    }
    void load()
  }, [])

  if (loading) {
    return (
      <div className="column column-center">
        <div className="bau page-pad">
          <p className="subtle">Loading BAU data…</p>
        </div>
      </div>
    )
  }

  return (
    <div className="column column-center">
      <div className="bau page-pad">
        <div className="bau__header">
          <div>
            <p className="eyebrow">BAU</p>
            <h2>BAU Hub</h2>
            <p className="lede">Daily enterprise workflows powered by durable execution + memory + governance.</p>
          </div>
          <div className="bau__actions">
            <button className="primary" onClick={() => navigate('/validation/golden-thread')}>Run golden thread</button>
            <button className="ghost" onClick={() => navigate('/sources')}>Ingest new doc</button>
            <button className="ghost" onClick={() => navigate('/evidence')}>View SLOs</button>
          </div>
        </div>

        <div className="bau__grid">
          <section className="panel">
            <div className="panel-head">
              <div>
                <p className="eyebrow">Daily flows</p>
                <h4>Choose a workflow</h4>
              </div>
            </div>

            <div className="flow-grid">
              {flows.map((f) => (
                <div key={f.id} className="flow-card">
                  <div className="flow-top">
                    <span className="pill muted">{f.persona}</span>
                  </div>
                  <h3>{f.title}</h3>
                  <p className="subtle">{f.description}</p>
                  <button
                    className="primary sm"
                    onClick={async () => {
                      try {
                        const { workflow_id } = await startBauFlow(f.id)
                        navigate(`/workflows/${workflow_id}`)
                      } catch (error) {
                        console.error('Failed to start BAU flow:', error)
                        alert(`Failed to start flow: ${error instanceof Error ? error.message : 'Unknown error'}`)
                      }
                    }}
                  >
                    {f.cta}
                  </button>
                </div>
              ))}
            </div>
          </section>

          <section className="panel">
            <div className="panel-head">
              <div>
                <p className="eyebrow">Recent artifacts</p>
                <h4>What changed recently</h4>
              </div>
            </div>

            <ul className="artifact-list">
              {artifacts.map((a) => (
                <li key={a.id} className="artifact">
                  <div>
                    <strong>{a.name}</strong>
                    <p className="subtle">{a.ingestedLabel}</p>
                    <div className="chip-row">
                      {a.chips.map((c) => (
                        <span key={c} className="chip">{c}</span>
                      ))}
                    </div>
                  </div>
                  <button className="ghost sm" onClick={() => navigate('/memory/search')}>Open</button>
                </li>
              ))}
            </ul>

            <div className="callout">
              <strong>Guided walkthrough</strong>
              <ol>
                <li>Ingest a real artifact</li>
                <li>Validate retrieval</li>
                <li>Run a workflow</li>
                <li>Review the evidence bundle</li>
              </ol>
              <button className="primary sm" onClick={() => navigate('/sources')}>Start walkthrough</button>
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
