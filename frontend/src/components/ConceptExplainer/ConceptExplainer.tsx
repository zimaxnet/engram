import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import '../../App.css';

interface ConceptContent {
    title: string;
    image: string;
    content: React.ReactNode;
}

const CONTENT_MAP: Record<string, ConceptContent> = {
    // Home route removed to prevent sidebar clutter
    // '/agents': { ... } could be added here if we want sidebar info on the agents page too
    '/memory/graph': {
        title: 'The Connective Tissue',
        image: '/assets/images/concept-graph.png',
        content: (
            <>
                <p>
                    <strong>Knowledge Graphs</strong> represent the "Long-term Semantic Memory" of the system.
                </p>
                <p>
                    Unlike vector databases which find "similar" text, graphs capture <em>relationships</em>. This allows the AI to reason about how entities (people, projects, concepts) are interconnected, enabling multi-hop reasoning that mimics human understanding.
                </p>
            </>
        )
    },
    '/memory/episodes': {
        title: 'Temporal Grounding',
        image: '/assets/images/concept-episodes.png',
        content: (
            <>
                <p>
                    <strong>Episodic Memory</strong> provides the "autobiography" of the AI's interactions.
                </p>
                <p>
                    By organizing interactions into time-bound episodes, the system maintains continuity. It prevents the AI from forgetting past context or effectively "waking up with amnesia" at the start of every session.
                </p>
            </>
        )
    },
    '/memory/search': {
        title: 'Hybrid Recall',
        image: '/assets/images/concept-search.png',
        content: (
            <>
                <p>
                    <strong>Semantic Search</strong> bridges the gap between exact keywords and conceptual meaning.
                </p>
                <p>
                    Zep uses hybrid search (dense vectors + sparse keywords) to retrieve relevant context. This ensures that when you ask about "that project from last week", the system knows exactly what you mean.
                </p>
            </>
        )
    },
    '/workflows': {
        title: 'Durable Execution',
        image: '/assets/images/concept-workflows.png',
        content: (
            <>
                <p>
                    <strong>Workflows</strong> are the "Spine" of agentic behavior.
                </p>
                <p>
                    Using Temporal.io, these processes are guaranteed to complete, even if servers fail. They allow agents to perform long-running tasks (like research or ETL) reliably, decoupling "thinking" from "acting".
                </p>
            </>
        )
    },
    '/settings': {
        title: 'System Control',
        image: '/assets/images/concept-settings.png',
        content: (
            <>
                <p>
                    <strong>Configuration</strong> governs the behavior of the cognitive architecture.
                </p>
                <p>
                    Here you define the boundaries—which models are available, default parameters, and integration points. It is the control plane for the entire synthetic brain.
                </p>
            </>
        )
    },
    '/admin': {
        title: 'Observability',
        image: '/assets/images/concept-admin.png',
        content: (
            <>
                <p>
                    <strong>Admin & Health</strong> provides a window into the system's operational state.
                </p>
                <p>
                    Monitoring health checks, user access, and audit logs ensures that the "Cognition-as-a-Service" platform remains secure, performant, and accountable.
                </p>
            </>
        )
    }
};

export function ConceptExplainer() {
    const location = useLocation();
    const [isModalOpen, setIsModalOpen] = useState(false);

    // Simple matching logic - checking if path starts with key for broader matches if needed,
    // or exact matches. For now, we essentially do exact or "best fit".
    // We can default to the root content if nothing matches specifically.

    let content: ConceptContent | null = null;

    // Find best matching path (longest prefix match)
    const sortedKeys = Object.keys(CONTENT_MAP).sort((a, b) => b.length - a.length);
    for (const key of sortedKeys) {
        if (location.pathname === key || (key !== '/' && location.pathname.startsWith(key))) {
            content = CONTENT_MAP[key];
            break;
        }
    }

    // Escape Handler
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape' && isModalOpen) {
                setIsModalOpen(false);
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isModalOpen]);

    if (!content) return null;

    return (
        <aside className="column column-right">
            <div className="concept-explainer">
                <div className="explainer-header">
                    <h3>{content.title}</h3>
                    <div className="explainer-icon">💡</div>
                </div>
                <div
                    className="explainer-image"
                    onClick={() => setIsModalOpen(true)}
                    role="button"
                    tabIndex={0}
                    title="Click to expand"
                    onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                            setIsModalOpen(true);
                        }
                    }}
                >
                    <img src={content.image} alt={content.title} />
                    <div className="explainer-image-overlay">
                        <span>🔍 Expand</span>
                    </div>
                </div>
                <div className="explainer-body">
                    {content.content}
                </div>
            </div>

            {/* Modal Overlay */}
            {isModalOpen && (
                <div className="image-modal-overlay" onClick={() => setIsModalOpen(false)}>
                    <div className="image-modal-content" onClick={(e) => e.stopPropagation()}>
                        <button
                            className="image-modal-close"
                            onClick={() => setIsModalOpen(false)}
                            aria-label="Close image"
                        >
                            ×
                        </button>
                        <img src={content.image} alt={content.title} />
                        <div className="image-modal-caption">
                            {content.title}
                        </div>
                    </div>
                </div>
            )}
        </aside>
    );
}
