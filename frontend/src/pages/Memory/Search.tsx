import { useMemo, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import { searchMemory } from '../../services/api';

interface SearchResult {
    id: string;
    content: string;
    node_type: string;
    confidence: number;
    created_at: string;
    metadata: Record<string, unknown>;
}

function chipEntries(result: SearchResult): string[] {
    const md = result.metadata || {};
    const filename = typeof md['filename'] === 'string' ? md['filename'] : null;
    const source = typeof md['source'] === 'string' ? md['source'] : null;
    const tenant = typeof md['tenant_id'] === 'string' ? md['tenant_id'] : typeof md['tenant'] === 'string' ? md['tenant'] : null;
    const domain = typeof md['domain'] === 'string' ? md['domain'] : null;
    const project = typeof md['project'] === 'string' ? md['project'] : null;
    const sensitivity = typeof md['sensitivity'] === 'string' ? md['sensitivity'] : null;

    const chips = [];
    if (filename) chips.push(`filename:${filename}`);
    if (source) chips.push(`source:${source}`);
    if (tenant) chips.push(`tenant:${tenant}`);
    if (domain) chips.push(`domain:${domain}`);
    if (project) chips.push(`project:${project}`);
    if (sensitivity) chips.push(`sensitivity:${sensitivity}`);
    chips.push(`created:${new Date(result.created_at).toLocaleDateString()}`);
    return chips;
}

export function Search() {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<SearchResult[]>([]);
    const [loading, setLoading] = useState(false);
    const [searched, setSearched] = useState(false);
    const [selectedId, setSelectedId] = useState<string | null>(null);

    const handleSearch = async () => {
        if (!query.trim()) return;

        setLoading(true);
        setSearched(true);
        try {
            const data = await searchMemory(query);
            setResults(data.results);
            setSelectedId(data.results?.[0]?.id ?? null);
        } catch (err) {
            console.error('Search failed:', err);
        } finally {
            setLoading(false);
        }
    };

    const selected = useMemo(
        () => results.find((r) => r.id === selectedId) ?? null,
        [results, selectedId]
    );

    return (
        <div className="column column-center">
            <div style={{ padding: '2rem', color: 'var(--color-text)' }}>
                <p style={{ fontSize: '0.75rem', letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--color-text-muted)' }}>Memory</p>
                <h2>Search (Provenance-first)</h2>
                <p style={{ marginTop: '0.5rem' }}>
                    Results are tenant-scoped and provenance-tagged. Use chips to verify grounding and source.
                </p>

                <div style={{
                    display: 'flex',
                    gap: '1rem',
                    marginTop: '1rem',
                    marginBottom: '1.25rem'
                }}>
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                        placeholder="Search facts, episodes, and documents…"
                        style={{
                            flex: 1,
                            padding: '0.75rem',
                            background: 'var(--glass-bg)',
                            border: '1px solid var(--glass-border)',
                            color: 'var(--color-text)',
                            borderRadius: '8px'
                        }}
                    />
                    <button
                        onClick={handleSearch}
                        disabled={loading}
                        style={{
                            padding: '0.75rem 1.25rem',
                            background: 'var(--color-primary)',
                            color: '#0b1020',
                            border: 'none',
                            borderRadius: '8px',
                            cursor: loading ? 'not-allowed' : 'pointer',
                            opacity: loading ? 0.7 : 1,
                            fontWeight: 800
                        }}
                    >
                        {loading ? 'Searching…' : 'Search'}
                    </button>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 0.8fr', gap: '1rem' }}>
                    {!searched && (
                        <p style={{ opacity: 0.7, textAlign: 'center' }}>Enter a query to search semantic memory.</p>
                    )}

                    {searched && !loading && results.length === 0 && (
                        <p style={{ textAlign: 'center' }}>No results found.</p>
                    )}

                    <div>
                        {results.map(result => {
                            const active = result.id === selectedId;
                            const chips = chipEntries(result);
                            return (
                                <button
                                    key={result.id}
                                    onClick={() => setSelectedId(result.id)}
                                    style={{
                                        width: '100%',
                                        textAlign: 'left',
                                        padding: '1rem',
                                        background: active ? 'rgba(0,0,0,0.25)' : 'var(--glass-bg)',
                                        border: active ? '1px solid rgba(0,212,255,0.35)' : '1px solid var(--glass-border)',
                                        marginBottom: '1rem',
                                        borderRadius: '12px',
                                        cursor: 'pointer',
                                        color: 'var(--color-text)'
                                    }}
                                >
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', gap: '0.75rem' }}>
                                        <span style={{
                                            textTransform: 'uppercase',
                                            fontSize: '0.75em',
                                            padding: '2px 8px',
                                            borderRadius: '999px',
                                            border: '1px solid var(--glass-border)',
                                            background: 'rgba(255,255,255,0.04)'
                                        }}>{result.node_type}</span>
                                        <span style={{ opacity: 0.7, fontSize: '0.8em' }}>
                                            Confidence: {(result.confidence * 100).toFixed(0)}%
                                        </span>
                                    </div>
                                    <div style={{ marginBottom: '0.75rem', color: 'var(--color-text)', lineHeight: '1.5' }}>
                                        <ReactMarkdown
                                            remarkPlugins={[remarkGfm]}
                                            rehypePlugins={[rehypeRaw]}
                                            components={{
                                                img: ({ node, ...props }) => <img {...props} style={{ maxWidth: '100%', borderRadius: '8px', border: '1px solid var(--glass-border)', marginTop: '0.5rem' }} />,
                                                a: ({ node, ...props }) => <a {...props} style={{ color: 'var(--color-primary)', textDecoration: 'none' }} target="_blank" rel="noopener noreferrer" />,
                                                p: ({ node, ...props }) => <p {...props} style={{ margin: '0.5rem 0' }} />
                                            }}
                                        >
                                            {result.content}
                                        </ReactMarkdown>
                                    </div>
                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                                        {chips.slice(0, 6).map((c) => (
                                            <span key={c} style={{
                                                border: '1px solid var(--glass-border)',
                                                borderRadius: '999px',
                                                padding: '0.2rem 0.55rem',
                                                background: 'rgba(0,0,0,0.18)',
                                                color: 'var(--color-text-dim)',
                                                fontSize: '0.8rem'
                                            }}>{c}</span>
                                        ))}
                                    </div>
                                </button>
                            )
                        })}
                    </div>

                    <aside style={{
                        background: 'var(--glass-bg)',
                        border: '1px solid var(--glass-border)',
                        borderRadius: '12px',
                        padding: '1rem',
                        height: 'fit-content'
                    }}>
                        <h4 style={{ marginBottom: '0.5rem' }}>Why this result?</h4>
                        {!selected && <p style={{ opacity: 0.7 }}>Select a result to see retrieval and provenance details.</p>}
                        {selected && (
                            <>
                                <div style={{ marginBottom: '0.75rem' }}>
                                    <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.12em' }}>Matched anchors</p>
                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.25rem' }}>
                                        {[query, 'provenance', 'tenant-scope'].filter(Boolean).map((t) => (
                                            <span key={t} style={{
                                                border: '1px solid var(--glass-border)',
                                                borderRadius: '999px',
                                                padding: '0.2rem 0.55rem',
                                                background: 'rgba(0,0,0,0.18)',
                                                color: 'var(--color-text-dim)',
                                                fontSize: '0.8rem'
                                            }}>{t}</span>
                                        ))}
                                    </div>
                                </div>

                                <div style={{ marginBottom: '0.75rem' }}>
                                    <p style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.12em' }}>Provenance</p>
                                    <ul style={{ marginLeft: '1.25rem', color: 'var(--color-text-dim)' }}>
                                        {chipEntries(selected).slice(0, 6).map((c) => <li key={c}>{c}</li>)}
                                    </ul>
                                </div>

                                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                    <button className="btn btn-ghost" type="button">Open in graph</button>
                                    <button className="btn btn-ghost" type="button">Copy citation</button>
                                </div>
                            </>
                        )}
                    </aside>
                </div>
            </div>
        </div>
    );
}
