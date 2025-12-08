import { useState } from 'react'
import type { Agent } from '../../App'
import AvatarDisplay from '../AvatarDisplay'
import VoiceChat from '../VoiceChat'
import './VisualPanel.css'

interface Viseme {
  time_ms: number;
  viseme_id: number;
}

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
  onVoiceMessage?: (message: { text: string; type: 'user' | 'agent' }) => void
}

export function VisualPanel({ agent, metrics, model, onModelChange, onVoiceMessage }: VisualPanelProps) {
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [currentVisemes, setCurrentVisemes] = useState<Viseme[]>([])
  const [expression, setExpression] = useState<'neutral' | 'smile' | 'thinking' | 'listening'>('neutral')
  const [voiceEnabled, setVoiceEnabled] = useState(true)
  
  const handleVisemes = (visemes: Viseme[]) => {
    setCurrentVisemes(visemes)
    setIsSpeaking(true)
    
    // Calculate total duration and stop speaking when done
    if (visemes.length > 0) {
      const lastViseme = visemes[visemes.length - 1]
      setTimeout(() => {
        setIsSpeaking(false)
        setCurrentVisemes([])
      }, lastViseme.time_ms + 500)
    }
  }
  
  const handleVoiceMessage = (message: { text: string; type: string }) => {
    if (message.type === 'user') {
      setExpression('thinking')
    } else {
      setExpression('neutral')
    }
    
    onVoiceMessage?.({
      text: message.text,
      type: message.type as 'user' | 'agent'
    })
  }

  return (
    <div className="visual-panel">
      {/* Agent Avatar Display with Voice */}
      <div className="panel-card avatar-card">
        <div className="card-header">
          <h4 className="card-title">Active Agent</h4>
          <button 
            className={`voice-toggle ${voiceEnabled ? 'enabled' : ''}`}
            onClick={() => setVoiceEnabled(!voiceEnabled)}
            title={voiceEnabled ? 'Disable voice' : 'Enable voice'}
          >
            {voiceEnabled ? '🔊' : '🔇'}
          </button>
        </div>
        
        {/* Avatar Component */}
        <AvatarDisplay
          agentId={agent.id as 'elena' | 'marcus'}
          isSpeaking={isSpeaking}
          expression={expression}
          visemes={currentVisemes}
          showName={true}
          size="lg"
        />
        
        {/* Voice Chat Component */}
        {voiceEnabled && (
          <div className="voice-section">
            <VoiceChat
              agentId={agent.id}
              onMessage={handleVoiceMessage}
              onVisemes={handleVisemes}
              disabled={!voiceEnabled}
            />
          </div>
        )}
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
            <span className="config-label">Voice</span>
            <select className="config-select">
              <option value="jenny">Jenny (Elena)</option>
              <option value="guy">Guy (Marcus)</option>
            </select>
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
