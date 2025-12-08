import type { Agent } from '../../App'
import './VisualPanel.css'

interface VisualPanelProps {
  agent: Agent
  metrics: {
    tokensUsed: number
    latency: number
    memoryNodes: number
    duration: number
    turns: number
    cost: number
  }
  model: string
  onModelChange: (model: string) => void
}

export function VisualPanel({ agent, metrics, model, onModelChange }: VisualPanelProps) {
  return (
    <div className="visual-panel">
      {/* Agent Avatar Display */}
      <div className="panel-card avatar-card">
        <h4 className="card-title">Agent Avatar Display</h4>
        <div 
          className="avatar-container"
          style={{ '--agent-color': agent.accentColor } as React.CSSProperties}
        >
          <img 
            src={agent.avatarUrl} 
            alt={agent.name}
            className="agent-avatar"
            onError={(e) => {
              (e.target as HTMLImageElement).src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200"><rect fill="%231a1f35" width="200" height="200"/><circle cx="100" cy="80" r="40" fill="%233b82f6"/><ellipse cx="100" cy="180" rx="60" ry="50" fill="%233b82f6"/></svg>'
            }}
          />
          <div className="avatar-waveform">
            <div className="waveform-bar"></div>
            <div className="waveform-bar"></div>
            <div className="waveform-bar"></div>
            <div className="waveform-bar"></div>
            <div className="waveform-bar"></div>
          </div>
        </div>
        <div className="avatar-info">
          <span className="avatar-name">{agent.name}</span>
          <span className="avatar-title">{agent.title}</span>
        </div>
      </div>

      {/* Session Metrics */}
      <div className="panel-card metrics-card">
        <h4 className="card-title">Session Metrics</h4>
        <div className="metrics-grid">
          <div className="metric">
            <span className="metric-icon">🪙</span>
            <div className="metric-data">
              <span className="metric-value">{metrics.tokensUsed.toLocaleString()}</span>
              <span className="metric-label">Tokens Used</span>
            </div>
          </div>
          <div className="metric">
            <span className="metric-icon">⚡</span>
            <div className="metric-data">
              <span className="metric-value">{metrics.latency.toFixed(1)}s</span>
              <span className="metric-label">Latency</span>
            </div>
          </div>
          <div className="metric">
            <span className="metric-icon">🔗</span>
            <div className="metric-data">
              <span className="metric-value">{metrics.memoryNodes}</span>
              <span className="metric-label">Memory Nodes</span>
            </div>
          </div>
          <div className="metric">
            <span className="metric-icon">⏱️</span>
            <div className="metric-data">
              <span className="metric-value">{metrics.duration}m</span>
              <span className="metric-label">Duration</span>
            </div>
          </div>
          <div className="metric">
            <span className="metric-icon">💬</span>
            <div className="metric-data">
              <span className="metric-value">{metrics.turns}</span>
              <span className="metric-label">Turns</span>
            </div>
          </div>
          <div className="metric">
            <span className="metric-icon">💵</span>
            <div className="metric-data">
              <span className="metric-value">${metrics.cost.toFixed(4)}</span>
              <span className="metric-label">Est. Cost</span>
            </div>
          </div>
        </div>
      </div>

      {/* Model Configuration */}
      <div className="panel-card config-card">
        <h4 className="card-title">Model Configuration</h4>
        <div className="config-content">
          <div className="config-row">
            <span className="config-label">Model</span>
            <select 
              value={model}
              onChange={(e) => onModelChange(e.target.value)}
              className="config-select"
            >
              <option value="gpt-4o">gpt-4o</option>
              <option value="gpt-4o-mini">gpt-4o-mini</option>
              <option value="gpt-4-turbo">gpt-4-turbo</option>
            </select>
          </div>
          <div className="config-row">
            <span className="config-label">Temperature</span>
            <div className="config-slider-container">
              <input 
                type="range" 
                min="0" 
                max="100" 
                defaultValue="70"
                className="config-slider"
              />
              <span className="config-value">0.7</span>
            </div>
          </div>
          <div className="config-row">
            <span className="config-label">Max Tokens</span>
            <div className="config-slider-container">
              <input 
                type="range" 
                min="0" 
                max="100" 
                defaultValue="80"
                className="config-slider"
              />
              <span className="config-value">4096</span>
            </div>
          </div>
          <div className="config-row">
            <span className="config-label">Top P</span>
            <div className="config-slider-container">
              <input 
                type="range" 
                min="0" 
                max="100" 
                defaultValue="95"
                className="config-slider"
              />
              <span className="config-value">0.95</span>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="panel-card actions-card">
        <button className="action-button">
          <span>📋</span> Export Chat
        </button>
        <button className="action-button">
          <span>🔄</span> Reset Context
        </button>
        <button className="action-button danger">
          <span>🗑️</span> Clear Memory
        </button>
      </div>
    </div>
  )
}

