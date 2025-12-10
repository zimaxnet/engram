import { AGENTS } from '../../types';

export function AgentsPage() {
    return (
        <div className="column column-center">
            <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto', color: 'var(--color-text)' }}>
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '1rem',
                    marginBottom: '2rem',
                    borderBottom: '1px solid var(--glass-border)',
                    paddingBottom: '1rem'
                }}>
                    <span style={{ fontSize: '2rem' }}>🧠</span>
                    <div>
                        <h2 style={{ margin: 0 }}>Specialized Personas</h2>
                        <p style={{ margin: 0, opacity: 0.7 }}>Cognition-as-a-Service Agents</p>
                    </div>
                </div>

                <div style={{ marginBottom: '3rem' }}>
                    <p style={{ fontSize: '1.1rem', lineHeight: '1.6' }}>
                        <strong>Cognition-as-a-Service</strong> relies on specialized agents, not generic chatbots.
                        Each persona is tuned with specific system prompts, temperature settings, and tool access to perform distinct cognitive tasks—from creative ideation to rigorous logic availability.
                    </p>

                    <div style={{ marginTop: '2rem' }}>
                        <img
                            src="/assets/images/concept-personas.png"
                            alt="Specialized Personas Diagram"
                            style={{
                                width: '100%',
                                borderRadius: '8px',
                                border: '1px solid var(--glass-border)',
                                boxShadow: '0 4px 20px rgba(0,0,0,0.2)'
                            }}
                        />
                    </div>
                </div>

                <h3>Available Agents</h3>
                <div style={{ display: 'grid', gap: '1.5rem', marginTop: '1.5rem' }}>
                    {Object.values(AGENTS).map(agent => (
                        <div key={agent.id} style={{
                            display: 'flex',
                            gap: '1.5rem',
                            padding: '1.5rem',
                            background: 'var(--glass-bg)',
                            border: '1px solid var(--glass-border)',
                            borderRadius: '12px'
                        }}>
                            <img
                                src={agent.avatarUrl}
                                alt={agent.name}
                                style={{ width: '80px', height: '80px', borderRadius: '50%', objectFit: 'cover' }}
                            />
                            <div>
                                <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '1.2rem', color: agent.accentColor }}>{agent.name}</h4>
                                <div style={{
                                    display: 'inline-block',
                                    padding: '0.25rem 0.75rem',
                                    background: 'rgba(255,255,255,0.1)',
                                    borderRadius: '20px',
                                    fontSize: '0.85rem',
                                    marginBottom: '1rem'
                                }}>
                                    {agent.title}
                                </div>
                                <p style={{ margin: 0, opacity: 0.8, lineHeight: '1.5' }}>
                                    {agent.description || "A specialized AI agent tuned for specific cognitive tasks within the Engram architecture."}
                                </p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
