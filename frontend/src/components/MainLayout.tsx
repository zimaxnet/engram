import { Outlet } from 'react-router-dom';
import { TreeNav } from './TreeNav/TreeNav';
import { AGENTS, type AgentId } from '../types';
import { ConceptExplainer } from './ConceptExplainer/ConceptExplainer';
import '../App.css';

interface MainLayoutProps {
    activeAgent: AgentId;
    onAgentChange: (agent: AgentId) => void;
    selectedModel: string;
    onModelChange: (model: string) => void;
}

export function MainLayout({
    activeAgent,
    onAgentChange,
    selectedModel,
    onModelChange
}: MainLayoutProps) {
    const agent = AGENTS[activeAgent];

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
                            onChange={(e) => onModelChange(e.target.value)}
                            className="model-dropdown"
                            title="Select Model"
                        >
                            <option value="gpt-5-chat">gpt-5-chat</option>
                        </select>
                    </div>
                    <div className="user-avatar">
                        <span>👤</span>
                    </div>
                </div>
            </header>

            <main className="main-content">
                <aside className="column column-left">
                    <TreeNav activeAgent={activeAgent} onAgentChange={onAgentChange} />
                </aside>

                {/* Render child routes (ChatView, etc.) with context */}
                <Outlet context={{ agent, selectedModel, onModelChange }} />

                <ConceptExplainer />
            </main>
        </div>
    );
}
