import { useEffect, useMemo, useState } from 'react'
import { getMemoryGraph } from '../../services/api'

type GraphNode = {
    id: string
    content: string
    node_type: string
    degree: number
    metadata: Record<string, unknown>
}

type GraphEdge = {
    id: string
    source: string
    target: string
    label?: string | null
    weight: number
}

type PositionedNode = GraphNode & { x: number; y: number }

const palette: Record<string, string> = {
    fact: '#60a5fa',
    memory: '#f59e0b',
    entity: '#34d399',
}

export function KnowledgeGraph() {
    const [nodes, setNodes] = useState<GraphNode[]>([])
    const [edges, setEdges] = useState<GraphEdge[]>([])
    const [loading, setLoading] = useState(true)
    const [query, setQuery] = useState('')
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        const fetchGraph = async () => {
            setLoading(true)
            setError(null)
            try {
                const data = await getMemoryGraph(query)
                setNodes(data.nodes || [])
                setEdges(data.edges || [])
            } catch (err) {
                console.error('Failed to load knowledge graph:', err)
                setError('Unable to load graph data right now.')
            } finally {
                setLoading(false)
            }
        }

        void fetchGraph()
    }, [query])

    const layout = useMemo(() => {
        const width = 960
        const height = 540
        const radius = Math.min(width, height) / 2 - 80
        const positioned: Record<string, PositionedNode> = {}

        const sortedNodes = [...nodes].sort((a, b) => a.node_type.localeCompare(b.node_type))
        sortedNodes.forEach((node, idx) => {
            const angle = (idx / Math.max(sortedNodes.length, 1)) * Math.PI * 2
            const x = width / 2 + radius * Math.cos(angle)
            const y = height / 2 + radius * Math.sin(angle)
            positioned[node.id] = { ...node, x, y }
        })

        return { width, height, nodes: positioned }
    }, [nodes])

    const nodeColor = (node: GraphNode) => palette[node.node_type] || '#c084fc'

    return (
        <div className="column column-center">
            <div style={{ padding: '2rem', color: 'var(--color-text)', width: '100%', maxWidth: '1100px' }}>
                <h2>Knowledge Graph</h2>
                <p>Live facts and metadata nodes derived from semantic memory.</p>

                <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', marginTop: '1rem' }}>
                    <input
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Filter facts (e.g., finance, contracts, sharepoint)"
                        style={{ flex: 1, padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid var(--glass-border)', background: 'var(--glass-bg)', color: 'inherit' }}
                    />
                    <span style={{ fontSize: '0.9rem', opacity: 0.75 }}>{nodes.length} nodes · {edges.length} edges</span>
                </div>

                <div style={{
                    marginTop: '1.5rem',
                    background: 'var(--glass-bg)',
                    border: '1px solid var(--glass-border)',
                    borderRadius: '12px',
                    padding: '1rem'
                }}>
                    {error && (
                        <div style={{ marginBottom: '0.75rem', color: '#f87171' }}>{error}</div>
                    )}
                    {loading && <div style={{ textAlign: 'center', padding: '2rem' }}>Loading graph...</div>}

                    {!loading && nodes.length > 0 && (
                        <div style={{ position: 'relative', width: '100%', overflow: 'hidden' }}>
                            <svg viewBox={`0 0 ${layout.width} ${layout.height}`} style={{ width: '100%', height: '520px' }}>
                                <defs>
                                    <marker id="arrow" markerWidth="10" markerHeight="10" refX="6" refY="3" orient="auto" markerUnits="strokeWidth">
                                        <path d="M0,0 L0,6 L9,3 z" fill="rgba(255,255,255,0.4)" />
                                    </marker>
                                </defs>

                                {edges.map((edge) => {
                                    const src = layout.nodes[edge.source]
                                    const tgt = layout.nodes[edge.target]
                                    if (!src || !tgt) return null
                                    return (
                                        <g key={edge.id}>
                                            <line
                                                x1={src.x}
                                                y1={src.y}
                                                x2={tgt.x}
                                                y2={tgt.y}
                                                stroke="rgba(255,255,255,0.35)"
                                                strokeWidth={Math.max(1, edge.weight)}
                                                markerEnd="url(#arrow)"
                                            />
                                            {edge.label && (
                                                <text x={(src.x + tgt.x) / 2} y={(src.y + tgt.y) / 2 - 6} fill="rgba(255,255,255,0.7)" fontSize="10" textAnchor="middle">
                                                    {edge.label}
                                                </text>
                                            )}
                                        </g>
                                    )
                                })}

                                {Object.values(layout.nodes).map((node) => (
                                    <g key={node.id}>
                                        <circle cx={node.x} cy={node.y} r={18} fill={nodeColor(node)} opacity={0.9} />
                                        <text x={node.x} y={node.y + 34} fill="rgba(255,255,255,0.85)" fontSize="11" textAnchor="middle">
                                            {node.node_type}
                                        </text>
                                        <title>{node.content}</title>
                                    </g>
                                ))}
                            </svg>
                        </div>
                    )}

                    {!loading && nodes.length === 0 && (
                        <div style={{ padding: '1rem', opacity: 0.8 }}>No graph nodes available yet. Add facts or ingest sources to populate memory.</div>
                    )}
                </div>

                {!loading && nodes.length > 0 && (
                    <div style={{ marginTop: '1rem', display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '1rem' }}>
                        {nodes.slice(0, 12).map((node) => (
                            <div key={node.id} style={{ border: '1px solid var(--glass-border)', borderRadius: '10px', padding: '0.75rem', background: 'rgba(255,255,255,0.04)' }}>
                                <div style={{ fontSize: '0.85rem', opacity: 0.75 }}>{node.node_type} · degree {node.degree}</div>
                                <div style={{ marginTop: '0.35rem', fontSize: '0.95rem' }}>{node.content}</div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}
