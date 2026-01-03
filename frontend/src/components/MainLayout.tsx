import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { TreeNav } from './TreeNav/TreeNav';
import { AGENTS, type AgentId } from '../types';
import { ConceptExplainer } from './ConceptExplainer/ConceptExplainer';
import { UserMenu } from './UserMenu/UserMenu';
import '../App.css';

interface MainLayoutProps {
    activeAgent: AgentId;
    onAgentChange: (agent: AgentId) => void;
    selectedModel: string;
    onModelChange: (model: string) => void;
    sessionId: string;
}

export function MainLayout({
    activeAgent,
    onAgentChange,
    selectedModel,
    onModelChange,
    sessionId
}: MainLayoutProps) {
    const agent = AGENTS[activeAgent];
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    return (
        <div className={`app-layout ${isMobileMenuOpen ? 'mobile-menu-open' : ''}`}>
            {/* Header */}
            <header className="app-header">
                <div className="header-left">
                    <button
                        className="mobile-menu-toggle"
                        onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                        aria-label="Toggle menu"
                    >
                        ☰
                    </button>
                    <div className="logo">ENGRAM</div>
                </div>
                <div className="header-controls">
                    <div className="model-selector">
                        <span className="model-icon">⚡</span>
                        <select
                            value={selectedModel}
                            onChange={(e) => onModelChange(e.target.value)}
                            className="model-dropdown"
                            title="Select Model"
                        >
                            <option value="gpt-5.2-chat">GPT-5.2-chat</option>
                        </select>
                    </div>
                    <div className="user-menu-wrapper">
                        <UserMenu />
                    </div>
                </div>
            </header>

            <main className="main-content">
                <aside className={`column column-left ${isMobileMenuOpen ? 'visible' : ''}`}>
                    <div className="mobile-menu-header">
                        <span className="mobile-menu-title">Navigation</span>
                        <button className="mobile-menu-close" onClick={() => setIsMobileMenuOpen(false)}>×</button>
                    </div>
                    <TreeNav
                        activeAgent={activeAgent}
                        onAgentChange={(id) => {
                            onAgentChange(id);
                        }}
                        onNavigate={() => setIsMobileMenuOpen(false)}
                    />
                </aside>

                {/* Mobile overlay backdrop */}
                {isMobileMenuOpen && (
                    <div className="mobile-menu-backdrop" onClick={() => setIsMobileMenuOpen(false)} />
                )}

                {/* Render child routes (ChatView, etc.) with context */}
                <Outlet context={{ agent, selectedModel, onModelChange, sessionId }} />

                <ConceptExplainer />
            </main>
        </div>
    );
}
