import { useState } from 'react'
import './App.css'
import { TreeNav } from './components/TreeNav/TreeNav'
import { ChatPanel } from './components/ChatPanel/ChatPanel'
import { VisualPanel } from './components/VisualPanel/VisualPanel'

export type AgentId = 'elena' | 'marcus'

export interface Agent {
  id: AgentId
  name: string
  title: string
  accentColor: string
  avatarUrl: string
}

const AGENTS: Record<AgentId, Agent> = {
  elena: {
    id: 'elena',
    name: 'Dr. Elena Vasquez',
    title: 'Business Analyst',
    accentColor: '#3b82f6',
    avatarUrl: '/assets/images/elena-portrait.png'
  },
  marcus: {
    id: 'marcus',
    name: 'Marcus Chen',
    title: 'Project Manager',
    accentColor: '#a855f7',
    avatarUrl: '/assets/images/marcus-portrait.png'
  }
}

function App() {
  const [activeAgent, setActiveAgent] = useState<AgentId>('elena')
  const [selectedModel, setSelectedModel] = useState('gpt-4o')
  const [sessionMetrics, setSessionMetrics] = useState({
    tokensUsed: 0,
    latency: 0,
    memoryNodes: 0,
    duration: 0,
    turns: 0,
    cost: 0
  })

  const agent = AGENTS[activeAgent]

  return (
    <div className="app-layout">
      {/* Header */}
      <header className="app-header">
        <div className="logo">ENGRAM</div>
        <div className="header-controls">
          <div className="model-selector">
            <span className="model-icon">⚡</span>
            <select 
              value={selectedModel} 
              onChange={(e) => setSelectedModel(e.target.value)}
              className="model-dropdown"
            >
              <option value="gpt-4o">gpt-4o</option>
              <option value="gpt-4o-mini">gpt-4o-mini</option>
              <option value="gpt-4-turbo">gpt-4-turbo</option>
            </select>
          </div>
          <div className="user-avatar">
            <span>👤</span>
          </div>
        </div>
      </header>

      {/* Main 3-Column Layout */}
      <main className="main-content">
        {/* Left Column - Tree Navigation */}
        <aside className="column column-left">
          <TreeNav 
            activeAgent={activeAgent}
            onAgentChange={setActiveAgent}
          />
        </aside>

        {/* Middle Column - Chat Interface */}
        <section className="column column-center">
          <ChatPanel 
            key={activeAgent}
            agent={agent}
            onMetricsUpdate={setSessionMetrics}
          />
        </section>

        {/* Right Column - Visual Panel */}
        <aside className="column column-right">
          <VisualPanel 
            agent={agent}
            metrics={sessionMetrics}
            model={selectedModel}
            onModelChange={setSelectedModel}
          />
        </aside>
      </main>
    </div>
  )
}

export default App
