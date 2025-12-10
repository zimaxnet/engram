import { useState, useEffect } from 'react';
import { listEpisodes, getEpisode } from '../../services/api';

interface Episode {
    id: string;
    summary: string;
    turn_count: number;
    agent_id: string;
    started_at: string;
    ended_at: string | null;
    topics: string[];
}

export function Episodes() {
    const [episodes, setEpisodes] = useState<Episode[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedTranscript, setSelectedTranscript] = useState<{ role: string; content: string }[] | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);

    useEffect(() => {
        const fetchEpisodes = async () => {
            try {
                const data = await listEpisodes();
                setEpisodes(data.episodes);
            } catch (err) {
                console.error('Failed to load episodes:', err);
                setError('Failed to load episodes');
            } finally {
                setLoading(false);
            }
        };
        fetchEpisodes();
    }, []);

    const handleViewContext = async (id: string) => {
        try {
            const data = await getEpisode(id);
            setSelectedTranscript(data.transcript);
            setIsModalOpen(true);
        } catch (err) {
            console.error('Failed to load context:', err);
        }
    };

    return (
        <div className="column column-center">
            <div style={{ padding: '2rem', color: 'var(--color-text)' }}>
                <h2>Episodes</h2>
                <p>Historical conversation episodes and summaries.</p>

                <div className="episodes-list" style={{ marginTop: '2rem' }}>
                    {loading && <p>Loading episodes...</p>}
                    {error && <p style={{ color: 'var(--color-accent-pink)' }}>{error}</p>}

                    {!loading && !error && episodes.length === 0 && (
                        <p style={{ opacity: 0.7 }}>No episodes found.</p>
                    )}

                    {episodes.map((episode: Episode) => (
                        <div key={episode.id} style={{
                            padding: '1rem',
                            background: 'var(--glass-bg)',
                            border: '1px solid var(--glass-border)',
                            marginBottom: '1rem',
                            borderRadius: '8px'
                        }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                <h4>{new Date(episode.started_at).toLocaleString()}</h4>
                                <span style={{ opacity: 0.7, fontSize: '0.9em' }}>{episode.turn_count} turns</span>
                            </div>
                            <p style={{ marginBottom: '0.5rem' }}><strong>Agent:</strong> {episode.agent_id}</p>
                            <p style={{ opacity: 0.9 }}>{episode.summary}</p>

                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '1rem' }}>
                                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                    {episode.topics.map((t: string) => (
                                        <span key={t} style={{
                                            background: 'rgba(255,255,255,0.1)',
                                            padding: '2px 8px',
                                            borderRadius: '10px',
                                            fontSize: '0.8em'
                                        }}>
                                            {t}
                                        </span>
                                    ))}
                                </div>
                                <button
                                    onClick={() => handleViewContext(episode.id)}
                                    style={{
                                        background: 'var(--color-primary)',
                                        border: 'none',
                                        padding: '0.5rem 1rem',
                                        borderRadius: '4px',
                                        color: '#fff',
                                        cursor: 'pointer',
                                        fontSize: '0.9em'
                                    }}
                                >
                                    View Context
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Transcript Modal */}
            {isModalOpen && selectedTranscript && (
                <div style={{
                    position: 'fixed',
                    top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.8)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    zIndex: 1000
                }} onClick={() => setIsModalOpen(false)}>
                    <div style={{
                        background: '#1a1a1a',
                        border: '1px solid var(--glass-border)',
                        padding: '2rem',
                        borderRadius: '8px',
                        maxWidth: '600px',
                        width: '90%',
                        maxHeight: '80vh',
                        overflowY: 'auto'
                    }} onClick={e => e.stopPropagation()}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                            <h3>Context Transcript</h3>
                            <button onClick={() => setIsModalOpen(false)} style={{ background: 'none', border: 'none', color: '#fff', cursor: 'pointer', fontSize: '1.2em' }}>×</button>
                        </div>
                        <div className="transcript-body">
                            {selectedTranscript.length === 0 ? (
                                <p style={{ opacity: 0.6 }}>No detailed transcript available for this episode.</p>
                            ) : (
                                selectedTranscript.map((msg: { role: string; content: string }, i: number) => (
                                    <div key={i} style={{ marginBottom: '1rem', paddingBottom: '1rem', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                                        <div style={{
                                            fontWeight: 'bold',
                                            color: msg.role === 'agent' ? 'var(--color-accent-cyan)' : 'var(--color-accent-pink)',
                                            marginBottom: '0.25rem',
                                            textTransform: 'capitalize'
                                        }}>
                                            {msg.role}
                                        </div>
                                        <div style={{ lineHeight: '1.5' }}>{msg.content}</div>
                                    </div>
                                ))
                            )}
                        </div>
                        <div style={{ marginTop: '1rem', textAlign: 'right' }}>
                            <button style={{
                                background: 'transparent',
                                border: '1px solid var(--color-primary)',
                                color: 'var(--color-primary)',
                                padding: '0.5rem 1rem',
                                borderRadius: '4px',
                                cursor: 'pointer'
                            }} onClick={() => {
                                // Mock action: In reality this would navigate to chat with sessionId=...
                                alert("Context loaded! (Simulation: This would start a chat with this context)");
                                setIsModalOpen(false);
                            }}>
                                Discuss with Agent
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
