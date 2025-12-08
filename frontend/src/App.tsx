import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [nodes, setNodes] = useState<{ id: number, x: number, y: number, r: number }[]>([])

  // Simple "Memory Node" Ambient Animation
  useEffect(() => {
    const initialNodes = Array.from({ length: 20 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      r: Math.random() * 5 + 2
    }))
    setNodes(initialNodes)

    const interval = setInterval(() => {
      setNodes(prev => prev.map(node => ({
        ...node,
        x: node.x + (Math.random() - 0.5) * 0.2,
        y: node.y + (Math.random() - 0.5) * 0.2
      })))
    }, 50)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="app-layout">
      {/* Ambient Background Layer */}
      <div className="ambient-bg">
        {nodes.map(node => (
          <div
            key={node.id}
            className="memory-node"
            style={{
              left: `${node.x}%`,
              top: `${node.y}%`,
              width: `${node.r}px`,
              height: `${node.r}px`
            } as React.CSSProperties}
          />
        ))}
      </div>

      {/* Main Content */}
      <nav className="glass-panel nav-bar">
        <div className="logo">ENGRAM</div>
        <div className="links">
          <a href="#">Architecture</a>
          <a href="#">Pricing</a>
          <a href="#" className="btn-small">Login</a>
        </div>
      </nav>

      <main className="hero-section">
        <div className="container">
          <h1 className="hero-title">
            Unlock <span className="gradient-text">Total Recall</span><br />
            For Your Enterprise
          </h1>
          <p className="hero-subtitle">
            The first Cognition-as-a-Service platform. Transform your scattered data into a enduring, reasoning Context Engine.
          </p>
          <div className="cta-group">
            <button className="btn-primary">Deploy Context Engine</button>
            <button className="btn-ghost">Read the Blueprint</button>
          </div>
        </div>
      </main>

      <section className="features container">
        <div className="glass-panel feature-card">
          <h3>Infinite Memory</h3>
          <p>Transcending the memory wall with Zep's Temporal Knowledge Graphs.</p>
        </div>
        <div className="glass-panel feature-card">
          <h3>Durable Execution</h3>
          <p>Orchestrate resilient agents that never forget a step with Temporal.</p>
        </div>
        <div className="glass-panel feature-card">
          <h3>Scale to Zero</h3>
          <p>Built for the modern FinOps era. Pay only for the thoughts you think.</p>
        </div>
      </section>
    </div>
  )
}

export default App
