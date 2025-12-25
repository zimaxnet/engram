import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import type { AgentId } from '../../types'
import './TreeNav.css'

interface TreeNavProps {
  activeAgent: AgentId
  onAgentChange: (agent: AgentId) => void
  onNavigate?: () => void
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
  path?: string // Add path property
  onClick?: () => void
}

export function TreeNav({ activeAgent, onAgentChange, onNavigate }: TreeNavProps) {
  const navigate = useNavigate();
  const location = useLocation();

  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['agents', 'chat-voice', 'ingestion', 'validation', 'memory', 'workflows', 'bau', 'settings', 'admin'])
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
      label: 'Cognition (Agents)',
      icon: '🧠',
      children: [
        { id: 'overview', label: 'Overview', icon: 'ℹ️', path: '/agents' },
        {
          id: 'elena',
          label: 'Elena - Analyst',
          status: activeAgent === 'elena' ? 'active' : 'idle',
          onClick: () => {
            onAgentChange('elena');
            navigate('/');
          }
        },
        {
          id: 'marcus',
          label: 'Marcus - PM',
          status: activeAgent === 'marcus' ? 'active' : 'idle',
          onClick: () => {
            onAgentChange('marcus');
            navigate('/');
          }
        },
        {
          id: 'sage',
          label: 'Sage - Storyteller',
          status: activeAgent === 'sage' ? 'active' : 'idle',
          onClick: () => {
            onAgentChange('sage');
            navigate('/');
          }
        },
        {
          id: 'stories',
          label: 'Stories (Artifacts)',
          icon: '📜',
          path: '/stories'
        }
      ]
    },
    {
      id: 'chat-voice',
      label: 'Chat & Voice',
      icon: '💬',
      children: [
        { id: 'chat', label: 'Chat (Episodic)', icon: '💬', path: '/' },
        { id: 'voice', label: 'Voice Interaction', icon: '🎤', path: '/voice' }
      ]
    },
    {
      id: 'ingestion',
      label: 'Ingestion',
      icon: '📥',
      children: [
        { id: 'sources', label: 'Overview', icon: '📊', path: '/sources' }
      ]
    },
    {
      id: 'validation',
      label: 'Evidence & Validation',
      icon: '✅',
      children: [
        { id: 'golden-thread', label: 'Golden Thread Runner', icon: '🧪', path: '/validation/golden-thread' },
        { id: 'evidence', label: 'Evidence & Telemetry', icon: '📡', path: '/evidence' }
      ]
    },
    {
      id: 'memory',
      label: 'Memory (Provenance-First)',
      icon: '💾',
      children: [
        { id: 'search', label: 'Search with Provenance', icon: '🔍', path: '/memory/search' },
        { id: 'episodes', label: 'Episodes (Episodic Memory)', icon: '📝', path: '/memory/episodes' },
        { id: 'graph', label: 'Knowledge Graph (Semantic)', icon: '🔗', path: '/memory/graph' }
      ]
    },
    {
      id: 'workflows',
      label: 'Workflows (Durable Spine)',
      icon: '⚡',
      children: [
        { id: 'active', label: 'Active Workflows', icon: '▶️', path: '/workflows/active' },
        { id: 'history', label: 'Workflow History', icon: '📋', path: '/workflows/history' },
        { id: 'signals', label: 'Signals & Events', icon: '🔔', path: '/workflows/signals' }
      ]
    },
    {
      id: 'bau',
      label: 'BAU',
      icon: '🏢',
      children: [
        { id: 'bau-hub', label: 'BAU Hub', icon: '🧭', path: '/bau' }
      ]
    },
    {
      id: 'settings',
      label: 'Settings',
      icon: '⚙️',
      children: [
        { id: 'general', label: 'General', icon: '🧩', path: '/settings/general' }
      ]
    },
    {
      id: 'admin',
      label: 'Admin',
      icon: '🛡️',
      children: [
        { id: 'users', label: 'Users', icon: '👥', path: '/admin/users' },
        { id: 'health', label: 'System Health', icon: '🩺', path: '/admin/health' }
      ]
    }
  ]

  const handleItemClick = (item: TreeItem) => {
    if (item.onClick) {
      item.onClick();
    } else if (item.path) {
      navigate(item.path);
    }

    // Always call onNavigate if provided to close mobile menu
    if (onNavigate) {
      onNavigate();
    }
  };

  const isItemActive = (item: TreeItem) => {
    if (item.status === 'active') return true;
    if (!item.path) return false;

    // Exact match for root path to avoid highlighting it on every page
    if (item.path === '/') {
      return location.pathname === '/';
    }

    return location.pathname.startsWith(item.path);
  };

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
                {section.children.map(item => {
                  const active = isItemActive(item);
                  return (
                    <li key={item.id}>
                      <button
                        className={`tree-item ${active ? 'active' : ''}`}
                        onClick={() => handleItemClick(item)}
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
                  );
                })}
              </ul>
            )}
          </div>
        ))}
      </div>
    </nav>
  )
}

