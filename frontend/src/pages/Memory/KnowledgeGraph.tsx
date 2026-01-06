import { useEffect, useState, useRef, useMemo, useCallback } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import { getMemoryEnvironments, getMemoryGraph } from '../../services/api'
import './KnowledgeGraph.css'

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

type GraphData = {
    nodes: GraphNode[]
    edges: GraphEdge[]
    stats?: {
        total_nodes: number
        total_edges: number
        node_types: Record<string, number>
        avg_degree: number
        max_degree: number
    }
}

type MemoryEnvironment = {
    name: string
    zep_api_url: string
    description: string
}

const NODE_COLORS: Record<string, string> = {
    fact: '#00d4ff',      // Cyan for facts
    entity: '#a855f7',    // Purple for entities
    memory: '#10b981',    // Green for episodic memory
    topic: '#f59e0b',     // Amber for topics
    meta: '#6b7280',      // Gray for metadata
}

const NODE_LABELS: Record<string, string> = {
    fact: 'Fact',
    entity: 'Entity',
    memory: 'Episode',
    topic: 'Topic',
    meta: 'Metadata',
}

export function KnowledgeGraph() {
    const [data, setData] = useState<GraphData>({ nodes: [], edges: [] })
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [query, setQuery] = useState('')
    const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
    const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null)
    const [showStats, setShowStats] = useState(true)
    const [filterNodeType, setFilterNodeType] = useState<string>('all')
    const [minDegree, setMinDegree] = useState(0)

    const [envLoading, setEnvLoading] = useState(false)
    const [environments, setEnvironments] = useState<MemoryEnvironment[]>([])
    const [activeZepUrl, setActiveZepUrl] = useState<string>('')

    const [lastQueryTimeMs, setLastQueryTimeMs] = useState<number | null>(null)
    const [lastLoadedAt, setLastLoadedAt] = useState<Date | null>(null)

    const containerRef = useRef<HTMLDivElement>(null)
    const graphRef = useRef<any>(null)
    const [dimensions, setDimensions] = useState({ width: 800, height: 600 })

    // Fetch graph data
    const fetchGraph = useCallback(async (searchQuery: string = '') => {
        setLoading(true)
        setError(null)
        try {
            const start = performance.now()
            const response = await getMemoryGraph(searchQuery)
            const elapsed = performance.now() - start
            setLastQueryTimeMs(elapsed)
            setLastLoadedAt(new Date())

            // Calculate statistics
            const nodeTypes: Record<string, number> = {}
            let totalDegree = 0
            let maxDegree = 0

            response.nodes.forEach(node => {
                nodeTypes[node.node_type] = (nodeTypes[node.node_type] || 0) + 1
                totalDegree += node.degree
                maxDegree = Math.max(maxDegree, node.degree)
            })

            const stats = {
                total_nodes: response.nodes.length,
                total_edges: response.edges.length,
                node_types: nodeTypes,
                avg_degree: response.nodes.length > 0 ? totalDegree / response.nodes.length : 0,
                max_degree: maxDegree,
            }

            setData({
                nodes: response.nodes,
                edges: response.edges,
                stats,
            })
        } catch (err) {
            console.error('Failed to load knowledge graph:', err)
            setError('Unable to load knowledge graph. Please try again.')
        } finally {
            setLoading(false)
        }
    }, [])

    // Fetch environment metadata (behind-the-veil visibility)
    useEffect(() => {
        let cancelled = false
        const load = async () => {
            setEnvLoading(true)
            try {
                const res = await getMemoryEnvironments()
                if (cancelled) return
                setActiveZepUrl(res.active_zep_api_url || '')
                setEnvironments(res.environments || [])
            } catch (e) {
                // Non-blocking: the graph can still render.
                if (cancelled) return
                setEnvironments([])
                setActiveZepUrl('')
            } finally {
                if (!cancelled) setEnvLoading(false)
            }
        }
        void load()
        return () => {
            cancelled = true
        }
    }, [])

    useEffect(() => {
        void fetchGraph(query)
    }, [fetchGraph, query])

    // Handle resizing
    useEffect(() => {
        const updateDimensions = () => {
            if (containerRef.current) {
                setDimensions({
                    width: containerRef.current.clientWidth,
                    height: window.innerHeight - 200
                })
            }
        }

        window.addEventListener('resize', updateDimensions)
        updateDimensions()

        return () => window.removeEventListener('resize', updateDimensions)
    }, [])

    // Filter nodes and edges based on filters
    const filteredData = useMemo(() => {
        let filteredNodes = data.nodes.filter(node => {
            if (filterNodeType !== 'all' && node.node_type !== filterNodeType) return false
            if (node.degree < minDegree) return false
            return true
        })

        const nodeIds = new Set(filteredNodes.map(n => n.id))
        const filteredEdges = data.edges.filter(edge =>
            nodeIds.has(edge.source) && nodeIds.has(edge.target)
        )

        return { nodes: filteredNodes, links: filteredEdges }
    }, [data, filterNodeType, minDegree])

    // Get connected nodes for selected node
    const connectedNodes = useMemo(() => {
        if (!selectedNode) return { nodes: [], edges: [] }

        const connectedIds = new Set<string>([selectedNode.id])
        const connectedEdges = data.edges.filter(edge =>
            edge.source === selectedNode.id || edge.target === selectedNode.id
        )

        connectedEdges.forEach(edge => {
            connectedIds.add(edge.source)
            connectedIds.add(edge.target)
        })

        const connectedNodes = data.nodes.filter(node => connectedIds.has(node.id))

        return { nodes: connectedNodes, edges: connectedEdges }
    }, [selectedNode, data])

    // Node size based on degree
    const getNodeSize = (node: GraphNode) => {
        if (!data.stats) return 5
        const normalizedDegree = data.stats.max_degree > 0
            ? node.degree / data.stats.max_degree
            : 0.5
        return 5 + normalizedDegree * 10
    }

    // Handle node click
    const handleNodeClick = useCallback((node: any) => {
        const graphNode = data.nodes.find(n => n.id === node.id)
        if (graphNode) {
            setSelectedNode(graphNode)
            // Center on node
            if (graphRef.current) {
                graphRef.current.centerAt(node.x, node.y, 1000)
                graphRef.current.zoom(2, 1000)
            }
        }
    }, [data.nodes])

    // Get unique node types
    const nodeTypes = useMemo(() => {
        const types = new Set(data.nodes.map(n => n.node_type))
        return Array.from(types).sort()
    }, [data.nodes])

    return (
        <div className="memory-graph-page">
            {/* Header */}
            <div className="memory-graph-header">
                <p style={{ fontSize: '0.75rem', letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--color-text-muted)' }}>
                    Memory
                </p>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginTop: '0.5rem' }}>
                    <div>
                        <h2>Gk (Graph Knowledge) — Tri-Search Graph Layer</h2>
                        <p style={{ marginTop: '0.5rem', opacity: 0.8, maxWidth: '800px' }}>
                            Explore entities, facts, and relationships extracted from conversations and documents.
                            Gk is the <strong>relationship layer</strong> of Engram’s tri-search capability, helping close the “what vs why” gap with provenance.
                        </p>
                    </div>
                    <button
                        onClick={() => setShowStats(!showStats)}
                        style={{
                            padding: '0.5rem 1rem',
                            background: showStats ? 'var(--color-primary)' : 'var(--glass-bg)',
                            border: '1px solid var(--glass-border)',
                            borderRadius: '8px',
                            color: showStats ? '#0b1020' : 'var(--color-text)',
                            cursor: 'pointer',
                            fontSize: '0.9rem'
                        }}
                    >
                        {showStats ? 'Hide' : 'Show'} Stats
                    </button>
                </div>
            </div>

            {/* Controls */}
            <div className="memory-graph-controls">
                <div style={{ flex: 1, minWidth: '300px' }}>
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Search graph by query (filters facts and episodes)..."
                        style={{
                            width: '100%',
                            padding: '0.75rem',
                            background: 'var(--glass-bg)',
                            border: '1px solid var(--glass-border)',
                            color: 'var(--color-text)',
                            borderRadius: '8px'
                        }}
                    />
                </div>
                <select
                    value={filterNodeType}
                    onChange={(e) => setFilterNodeType(e.target.value)}
                    style={{
                        padding: '0.75rem',
                        background: 'var(--glass-bg)',
                        border: '1px solid var(--glass-border)',
                        color: 'var(--color-text)',
                        borderRadius: '8px',
                        minWidth: '150px'
                    }}
                >
                    <option value="all">All Types</option>
                    {nodeTypes.map(type => (
                        <option key={type} value={type}>{NODE_LABELS[type] || type}</option>
                    ))}
                </select>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', minWidth: '200px' }}>
                    <label style={{ fontSize: '0.9rem', opacity: 0.8 }}>Min Degree:</label>
                    <input
                        type="number"
                        value={minDegree}
                        onChange={(e) => setMinDegree(parseInt(e.target.value) || 0)}
                        min="0"
                        style={{
                            width: '80px',
                            padding: '0.5rem',
                            background: 'var(--glass-bg)',
                            border: '1px solid var(--glass-border)',
                            color: 'var(--color-text)',
                            borderRadius: '8px'
                        }}
                    />
                </div>
            </div>

            {/* Main Content */}
            <div className="memory-graph-main">
                {/* Graph Visualization */}
                <div
                    ref={containerRef}
                    className="memory-graph-viz"
                >
                    {loading && (
                        <div style={{
                            position: 'absolute',
                            top: '50%',
                            left: '50%',
                            transform: 'translate(-50%, -50%)',
                            zIndex: 10,
                            background: 'var(--glass-bg)',
                            padding: '1rem 2rem',
                            borderRadius: '8px',
                            border: '1px solid var(--glass-border)'
                        }}>
                            <div className="loading-spinner">Loading Knowledge Graph...</div>
                        </div>
                    )}

                    {error && (
                        <div style={{
                            position: 'absolute',
                            top: '50%',
                            left: '50%',
                            transform: 'translate(-50%, -50%)',
                            color: 'red',
                            zIndex: 10,
                            background: 'var(--glass-bg)',
                            padding: '1rem 2rem',
                            borderRadius: '8px',
                            border: '1px solid var(--glass-border)'
                        }}>
                            {error}
                        </div>
                    )}

                    {!loading && !error && filteredData.nodes.length === 0 && (
                        <div style={{
                            position: 'absolute',
                            top: '50%',
                            left: '50%',
                            transform: 'translate(-50%, -50%)',
                            zIndex: 10,
                            textAlign: 'center',
                            opacity: 0.7
                        }}>
                            <p>No nodes match the current filters.</p>
                            <p style={{ fontSize: '0.9rem', marginTop: '0.5rem' }}>
                                Try adjusting filters or search query.
                            </p>
                        </div>
                    )}

                    {!loading && !error && filteredData.nodes.length > 0 && (
                        <ForceGraph2D
                            ref={graphRef}
                            width={dimensions.width}
                            height={dimensions.height}
                            graphData={filteredData}
                            nodeLabel={(node: any) => {
                                const graphNode = data.nodes.find(n => n.id === node.id)
                                return graphNode ? `${graphNode.content}\nType: ${graphNode.node_type}\nDegree: ${graphNode.degree}` : node.id
                            }}
                            nodeColor={(node: any) => {
                                const graphNode = data.nodes.find(n => n.id === node.id)
                                if (!graphNode) return '#ffffff'
                                if (selectedNode && node.id === selectedNode.id) return '#ffffff'
                                if (hoveredNode && node.id === hoveredNode.id) return '#ffffff'
                                return NODE_COLORS[graphNode.node_type] || '#6b7280'
                            }}
                            nodeVal={getNodeSize}
                            linkDirectionalArrowLength={4}
                            linkDirectionalArrowRelPos={1}
                            linkWidth={1}
                            linkColor={() => 'rgba(255,255,255,0.2)'}
                            backgroundColor="rgba(0,0,0,0)"
                            onNodeClick={handleNodeClick}
                            onNodeHover={(node: any) => {
                                const graphNode = data.nodes.find(n => n.id === node?.id)
                                setHoveredNode(graphNode || null)
                            }}
                            onNodeDragEnd={(node: any) => {
                                node.fx = node.x
                                node.fy = node.y
                            }}
                            nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
                                const graphNode = data.nodes.find(n => n.id === node.id)
                                if (!graphNode) return

                                const label = graphNode.content.length > 30
                                    ? graphNode.content.substring(0, 30) + '...'
                                    : graphNode.content
                                const fontSize = 12 / Math.sqrt(globalScale)
                                ctx.font = `${fontSize}px Sans-Serif`
                                const textWidth = ctx.measureText(label).width
                                const bckgDimensions = [textWidth + fontSize * 0.4, fontSize * 1.4]

                                const isSelected = selectedNode && node.id === selectedNode.id
                                const isHovered = hoveredNode && node.id === hoveredNode.id

                                ctx.fillStyle = isSelected
                                    ? 'rgba(0, 212, 255, 0.3)'
                                    : isHovered
                                        ? 'rgba(255, 255, 255, 0.2)'
                                        : 'rgba(0, 0, 0, 0.3)'

                                if (node.x && node.y) {
                                    ctx.fillRect(
                                        node.x - bckgDimensions[0] / 2,
                                        node.y - bckgDimensions[1] / 2,
                                        bckgDimensions[0],
                                        bckgDimensions[1]
                                    )
                                }

                                ctx.textAlign = 'center'
                                ctx.textBaseline = 'middle'
                                ctx.fillStyle = isSelected || isHovered ? '#ffffff' : 'rgba(255, 255, 255, 0.9)'
                                if (node.x && node.y) {
                                    ctx.fillText(label, node.x, node.y)
                                }
                            }}
                        />
                    )}
                </div>

                {/* Sidebar */}
                <div className="memory-graph-sidebar">
                    {/* Environments Panel */}
                    <div className="memory-graph-panel">
                        <h3 style={{ marginBottom: '0.75rem', fontSize: '1rem' }}>Environments</h3>
                        <p style={{ fontSize: '0.85rem', lineHeight: '1.6', marginBottom: '0.75rem', opacity: 0.9 }}>
                            Visibility into where memory is retrieved from.
                        </p>
                        <div style={{ fontSize: '0.85rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                            <div className="memory-graph-kv">
                                <span style={{ opacity: 0.8 }}>Active Zep URL:</span>
                                <strong style={{ overflowWrap: 'anywhere', textAlign: 'right' }}>{activeZepUrl || (envLoading ? 'Loading…' : 'Unknown')}</strong>
                            </div>
                            {environments.map(env => (
                                <div key={env.name} style={{ paddingTop: '0.5rem', borderTop: '1px solid var(--glass-border)' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem' }}>
                                        <strong>{env.name}</strong>
                                        <span style={{ opacity: 0.8, overflowWrap: 'anywhere', textAlign: 'right' }}>{env.zep_api_url}</span>
                                    </div>
                                    <div style={{ fontSize: '0.8rem', opacity: 0.75, marginTop: '0.25rem' }}>{env.description}</div>
                                </div>
                            ))}
                            {!envLoading && environments.length === 0 && (
                                <div style={{ opacity: 0.7 }}>No environment metadata available.</div>
                            )}
                        </div>
                    </div>

                    {/* Function Calls (Fc) Panel */}
                    <div className="memory-graph-panel">
                        <h3 style={{ marginBottom: '0.75rem', fontSize: '1rem' }}>Function Calls (Fc)</h3>
                        <p style={{ fontSize: '0.85rem', lineHeight: '1.6', marginBottom: '0.75rem', opacity: 0.9 }}>
                            The UI maps directly to API calls so you can “peer behind the veil”.
                        </p>
                        <div style={{ fontSize: '0.85rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                            <div>
                                <strong>GET</strong> <span style={{ opacity: 0.9 }}>/api/v1/memory/graph</span>
                                <div style={{ fontSize: '0.8rem', opacity: 0.75 }}>Params: query={query || '(empty)'}; client-side filters: type={filterNodeType}, minDegree={minDegree}</div>
                                <div style={{ fontSize: '0.8rem', opacity: 0.75 }}>
                                    Last load: {lastLoadedAt ? lastLoadedAt.toLocaleString() : '—'}; fetch: {lastQueryTimeMs != null ? `${Math.round(lastQueryTimeMs)}ms` : '—'}
                                </div>
                            </div>
                            <div style={{ paddingTop: '0.5rem', borderTop: '1px solid var(--glass-border)' }}>
                                <strong>GET</strong> <span style={{ opacity: 0.9 }}>/api/v1/memory/environments</span>
                                <div style={{ fontSize: '0.8rem', opacity: 0.75 }}>Used for: environment list + active Zep URL</div>
                            </div>
                        </div>
                    </div>

                    {/* Statistics Panel */}
                    {showStats && data.stats && (
                        <div className="memory-graph-panel">
                            <h3 style={{ marginBottom: '0.75rem', fontSize: '1rem' }}>Graph Statistics</h3>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.9rem' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span style={{ opacity: 0.8 }}>Total Nodes:</span>
                                    <strong>{data.stats.total_nodes}</strong>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span style={{ opacity: 0.8 }}>Total Edges:</span>
                                    <strong>{data.stats.total_edges}</strong>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span style={{ opacity: 0.8 }}>Avg Degree:</span>
                                    <strong>{data.stats.avg_degree.toFixed(1)}</strong>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span style={{ opacity: 0.8 }}>Max Degree:</span>
                                    <strong>{data.stats.max_degree}</strong>
                                </div>
                            </div>
                            <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--glass-border)' }}>
                                <p style={{ fontSize: '0.85rem', opacity: 0.8, marginBottom: '0.5rem' }}>Node Types:</p>
                                {Object.entries(data.stats.node_types).map(([type, count]) => (
                                    <div key={type} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                                        <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                            <span style={{
                                                width: '12px',
                                                height: '12px',
                                                borderRadius: '50%',
                                                background: NODE_COLORS[type] || '#6b7280'
                                            }} />
                                            {NODE_LABELS[type] || type}:
                                        </span>
                                        <strong>{count}</strong>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Node Details Panel */}
                    {selectedNode && (
                        <div className="memory-graph-panel">
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                                <h3 style={{ fontSize: '1rem' }}>Node Details</h3>
                                <button
                                    onClick={() => setSelectedNode(null)}
                                    style={{
                                        background: 'transparent',
                                        border: 'none',
                                        color: 'var(--color-text)',
                                        cursor: 'pointer',
                                        fontSize: '1.2rem',
                                        opacity: 0.7
                                    }}
                                >
                                    ×
                                </button>
                            </div>

                            <div style={{ marginBottom: '0.75rem' }}>
                                <span style={{
                                    display: 'inline-block',
                                    padding: '0.25rem 0.75rem',
                                    borderRadius: '999px',
                                    background: NODE_COLORS[selectedNode.node_type] || '#6b7280',
                                    color: '#0b1020',
                                    fontSize: '0.75rem',
                                    fontWeight: 'bold',
                                    textTransform: 'uppercase'
                                }}>
                                    {NODE_LABELS[selectedNode.node_type] || selectedNode.node_type}
                                </span>
                            </div>

                            <div style={{ marginBottom: '0.75rem' }}>
                                <p style={{ fontSize: '0.85rem', opacity: 0.8, marginBottom: '0.25rem' }}>Content:</p>
                                <p style={{ fontSize: '0.9rem', lineHeight: '1.5' }}>{selectedNode.content}</p>
                            </div>

                            <div style={{ marginBottom: '0.75rem' }}>
                                <p style={{ fontSize: '0.85rem', opacity: 0.8, marginBottom: '0.25rem' }}>Degree (Connections):</p>
                                <p style={{ fontSize: '0.9rem', fontWeight: 'bold' }}>{selectedNode.degree}</p>
                            </div>

                            {Object.keys(selectedNode.metadata || {}).length > 0 && (
                                <div style={{ marginBottom: '0.75rem' }}>
                                    <p style={{ fontSize: '0.85rem', opacity: 0.8, marginBottom: '0.25rem' }}>Metadata:</p>
                                    <div style={{ fontSize: '0.85rem' }}>
                                        {Object.entries(selectedNode.metadata).map(([key, value]) => (
                                            <div key={key} style={{ marginBottom: '0.25rem' }}>
                                                <strong>{key}:</strong> {String(value)}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {connectedNodes.edges.length > 0 && (
                                <div>
                                    <p style={{ fontSize: '0.85rem', opacity: 0.8, marginBottom: '0.25rem' }}>
                                        Connected Nodes ({connectedNodes.nodes.length - 1}):
                                    </p>
                                    <div style={{ maxHeight: '200px', overflowY: 'auto', fontSize: '0.85rem' }}>
                                        {connectedNodes.nodes
                                            .filter(n => n.id !== selectedNode.id)
                                            .slice(0, 10)
                                            .map(node => (
                                                <div
                                                    key={node.id}
                                                    onClick={() => handleNodeClick({ id: node.id })}
                                                    style={{
                                                        padding: '0.5rem',
                                                        marginBottom: '0.25rem',
                                                        background: 'rgba(0,0,0,0.2)',
                                                        borderRadius: '6px',
                                                        cursor: 'pointer',
                                                        border: '1px solid transparent'
                                                    }}
                                                    onMouseEnter={(e) => {
                                                        e.currentTarget.style.borderColor = NODE_COLORS[node.node_type] || '#6b7280'
                                                    }}
                                                    onMouseLeave={(e) => {
                                                        e.currentTarget.style.borderColor = 'transparent'
                                                    }}
                                                >
                                                    <div style={{ fontWeight: 'bold', marginBottom: '0.25rem' }}>
                                                        {node.content.length > 40 ? node.content.substring(0, 40) + '...' : node.content}
                                                    </div>
                                                    <span style={{
                                                        fontSize: '0.75rem',
                                                        opacity: 0.7
                                                    }}>
                                                        {NODE_LABELS[node.node_type] || node.node_type} • {node.degree} connections
                                                    </span>
                                                </div>
                                            ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Tri-Search Info Panel */}
                    <div style={{
                        background: 'var(--glass-bg)',
                        border: '1px solid var(--glass-border)',
                        borderRadius: '12px',
                        padding: '1rem'
                    }}>
                        <h3 style={{ marginBottom: '0.75rem', fontSize: '1rem' }}>Tri-Search Context</h3>
                        <p style={{ fontSize: '0.85rem', lineHeight: '1.6', marginBottom: '0.75rem', opacity: 0.9 }}>
                            This graph represents the <strong>Graph Knowledge (Gk)</strong> layer of Engram's tri-search capability:
                        </p>
                        <div style={{ fontSize: '0.85rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                            <div>
                                <strong>1. Keyword Search:</strong> Full-text matching in session content
                            </div>
                            <div>
                                <strong>2. Vector Search:</strong> Semantic similarity via embeddings
                            </div>
                            <div>
                                <strong>3. Graph Search:</strong> Relationship traversal (this view)
                            </div>
                        </div>
                        <p style={{ fontSize: '0.8rem', marginTop: '0.75rem', opacity: 0.7, fontStyle: 'italic' }}>
                            Results are combined using Reciprocal Rank Fusion (RRF) for optimal retrieval.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}
