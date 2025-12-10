import { useEffect, useState } from 'react';
import { searchMemory } from '../../services/api';

export function KnowledgeGraph() {
    const [facts, setFacts] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Fetch generic facts (using empty search for now to get top facts)
        // Or if backend supported getFacts directly. Using search "entitities" or "*"
        const fetchFacts = async () => {
            try {
                // Determine how to get random/top facts. " " might return all.
                const data = await searchMemory("");
                setFacts(data.results);
            } catch (err) {
                console.error('Failed to load knowledge graph:', err);
            } finally {
                setLoading(false);
            }
        }
        fetchFacts();
    }, []);

    return (
        <div className="column column-center">
            <div style={{ padding: '2rem', color: 'var(--color-text)' }}>
                <h2>Knowledge Graph</h2>
                <p>Semantic memory nodes (Facts & Entities).</p>

                <div style={{
                    marginTop: '2rem',
                    minHeight: '400px',
                    background: 'var(--glass-bg)',
                    border: '1px solid var(--glass-border)',
                    borderRadius: '8px',
                    padding: '1rem'
                }}>
                    {loading && <div style={{ textAlign: 'center', padding: '2rem' }}>Loading graph data...</div>}

                    {!loading && (
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem' }}>
                            {facts.map(fact => (
                                <div key={fact.id} style={{
                                    padding: '0.75rem',
                                    background: 'rgba(255,255,255,0.05)',
                                    borderRadius: '6px',
                                    border: '1px solid rgba(255,255,255,0.1)'
                                }}>
                                    <div style={{ fontSize: '0.8em', opacity: 0.6, marginBottom: '0.25rem' }}>
                                        {fact.node_type}
                                    </div>
                                    <div style={{ fontSize: '0.9em' }}>{fact.content}</div>
                                </div>
                            ))}
                            {facts.length === 0 && <p style={{ gridColumn: '1/-1', textAlign: 'center' }}>No knowledge nodes found.</p>}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
