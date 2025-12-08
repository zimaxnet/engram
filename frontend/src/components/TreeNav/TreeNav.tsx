import { useState } from 'react'
import type { AgentId } from '../../App'
import './TreeNav.css'

interface TreeNavProps {
  activeAgent: AgentId
  onAgentChange: (agent: AgentId) => void
}

interface TreeSection {
  id: string
  label: string
  icon: string
  expanded?: boolean
  children?: TreeItem[]
}

interface TreeItem {
  id: string
  label: string
  icon?: string
  status?: 'active' | 'idle' | 'warning'
  onClick?: () => void
}

export function TreeNav({ activeAgent, onAgentChange }: TreeNavProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['agents', 'memory'])
  )

  const toggleSection = (id: string) => {
    setExpandedSections(prev => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const sections: TreeSection[] = [
    {
      id: 'agents',
      label: 'Agents',
      icon: '🧠',
      children: [
        {
          id: 'elena',
          label: 'Elena - Analyst',
          status: activeAgent === 'elena' ? 'active' : 'idle',
          onClick: () => onAgentChange('elena')
        },
        {
          id: 'marcus',
          label: 'Marcus - PM',
          status: activeAgent === 'marcus' ? 'active' : 'idle',
          onClick: () => onAgentChange('marcus')
        }
      ]
    },
    {
      id: 'memory',
      label: 'Memory',
      icon: '💾',
      children: [
        { id: 'graph', label: 'Knowledge Graph', icon: '🔗' },
        { id: 'episodes', label: 'Episodes', icon: '📝' },
        { id: 'search', label: 'Search', icon: '🔍' }
      ]
    },
    {
      id: 'workflows',
      label: 'Workflows',
      icon: '⚡',
      children: [
        { id: 'active', label: 'Active', icon: '▶️' },
        { id: 'history', label: 'History', icon: '📋' },
        { id: 'signals', label: 'Signals', icon: '🔔' }
      ]
    },
    {
      id: 'settings',
      label: 'Settings',
      icon: '⚙️',
      children: [
        { id: 'model', label: 'Model', icon: '🤖' },
        { id: 'voice', label: 'Voice', icon: '🎤' },
        { id: 'rbac', label: 'RBAC', icon: '🔐' }
      ]
    },
    {
      id: 'admin',
      label: 'Admin',
      icon: '🛡️',
      children: [
        { id: 'users', label: 'Users', icon: '👥' },
        { id: 'audit', label: 'Audit Log', icon: '📊' },
        { id: 'cost', label: 'Cost', icon: '💰' }
      ]
    }
  ]

  return (
    <nav className="tree-nav">
      <div className="tree-nav-header">
        <h3>System Navigator</h3>
      </div>
      
      <div className="tree-nav-content">
        {sections.map(section => (
          <div key={section.id} className="tree-section">
            <button
              className="tree-section-header"
              onClick={() => toggleSection(section.id)}
            >
              <span className="tree-expand-icon">
                {expandedSections.has(section.id) ? '▼' : '▶'}
              </span>
              <span className="tree-section-icon">{section.icon}</span>
              <span className="tree-section-label">{section.label}</span>
            </button>
            
            {expandedSections.has(section.id) && section.children && (
              <ul className="tree-items">
                {section.children.map(item => (
                  <li key={item.id}>
                    <button
                      className={`tree-item ${item.status === 'active' ? 'active' : ''}`}
                      onClick={item.onClick}
                    >
                      {item.status && (
                        <span className={`status-dot ${item.status}`} />
                      )}
                      {item.icon && (
                        <span className="tree-item-icon">{item.icon}</span>
                      )}
                      <span className="tree-item-label">{item.label}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </nav>
  )
}

