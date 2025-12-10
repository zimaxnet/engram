import { useState } from 'react';
import { searchMemory } from '../../services/api';

interface SearchResult {
    id: string;
    content: string;
    node_type: string;
    confidence: number;
    created_at: string;
    metadata: Record<string, unknown>;
}

export function Search() {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<SearchResult[]>([]);
    const [loading, setLoading] = useState(false);
    const [searched, setSearched] = useState(false);

    const handleSearch = async () => {
        if (!query.trim()) return;

        setLoading(true);
        setSearched(true);
        try {
            const data = await searchMemory(query);
            setResults(data.results);
        } catch (err) {
            console.error('Search failed:', err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="column column-center">
            <div style={{ padding: '2rem', color: 'var(--color-text)' }}>
                <h2>Memory Search</h2>
                <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                        placeholder="Search memory..."
                        style={{
                            flex: 1,
                            padding: '0.75rem',
                            background: 'var(--glass-bg)',
                            border: '1px solid var(--glass-border)',
                            color: 'var(--color-text)',
                            borderRadius: '4px'
                        }}
                    />
                    <button
                        onClick={handleSearch}
                        disabled={loading}
                        style={{
                            padding: '0.75rem 1.5rem',
                            background: 'var(--color-primary)',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: loading ? 'not-allowed' : 'pointer',
                            opacity: loading ? 0.7 : 1
                        }}
                    >
                        {loading ? 'Searching...' : 'Search'}
                    </button>
                </div>

                <div className="search-results">
                    {!searched && (
                        <p style={{ opacity: 0.7, textAlign: 'center' }}>Enter a query to search semantic memory.</p>
                    )}

                    {searched && !loading && results.length === 0 && (
                        <p style={{ textAlign: 'center' }}>No results found.</p>
                    )}

                    {results.map(result => (
                        <div key={result.id} style={{
                            padding: '1rem',
                            background: 'var(--glass-bg)',
                            border: '1px solid var(--glass-border)',
                            marginBottom: '1rem',
                            borderRadius: '8px'
                        }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                <span style={{
                                    textTransform: 'uppercase',
                                    fontSize: '0.75em',
                                    padding: '2px 6px',
                                    borderRadius: '4px',
                                    background: 'rgba(255,255,255,0.1)'
                                }}>{result.node_type}</span>
                                <span style={{ opacity: 0.5, fontSize: '0.8em' }}>
                                    Confidence: {(result.confidence * 100).toFixed(0)}%
                                </span>
                            </div>
                            <p>{result.content}</p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
