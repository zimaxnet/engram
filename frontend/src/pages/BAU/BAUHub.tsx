import { useEffect, useState } from 'react'
import './BAUHub.css'
import { listBauFlows, listRecentArtifacts, type BauArtifact, type BauFlow } from '../../services/bau'

export function BAUHub() {
  const [flows, setFlows] = useState<BauFlow[]>([])
  const [artifacts, setArtifacts] = useState<BauArtifact[]>([])

  useEffect(() => {
    const load = async () => {
      const [f, a] = await Promise.all([listBauFlows(), listRecentArtifacts()])
      setFlows(f)
      setArtifacts(a)
    }
    void load()
  }, [])

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
            <button className="primary" onClick={() => alert('Wire to Golden Thread runner')}>Run golden thread</button>
            <button className="ghost" onClick={() => alert('Wire to Sources upload')}>Ingest new doc</button>
            <button className="ghost" onClick={() => alert('Wire to Evidence & Telemetry')}>View SLOs</button>
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
                  <button className="primary sm" onClick={() => alert(`Open flow: ${f.id}`)}>
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
                  <button className="ghost sm" onClick={() => alert('Open in Memory view')}>Open</button>
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
              <button className="primary sm" onClick={() => alert('Start walkthrough')}>Start walkthrough</button>
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
