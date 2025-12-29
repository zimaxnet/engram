import { useEffect, useState, useRef } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import { getGraphDump } from '../../services/api'

type GraphData = {
    nodes: Array<{ id: string;[key: string]: unknown }>
    links: Array<{ source: string; target: string;[key: string]: unknown }>
}

export function KnowledgeGraph() {
    const [data, setData] = useState<GraphData>({ nodes: [], links: [] })
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const containerRef = useRef<HTMLDivElement>(null)
    const [dimensions, setDimensions] = useState({ width: 800, height: 600 })

    useEffect(() => {
        const fetchGraph = async () => {
            setLoading(true)
            try {
                const response = await getGraphDump()
                const graphData = {
                    nodes: response.nodes.map(n => ({ ...n, val: 1 })), // standardizing
                    links: response.links || response.edges || [] // handling both naming conventions
                }
                setData(graphData)
            } catch (err) {
                console.error('Failed to load knowledge graph:', err)
                setError('Unable to load knowledge graph.')
            } finally {
                setLoading(false)
            }
        }

        void fetchGraph()
    }, [])

    // Handle resizing
    useEffect(() => {
        const updateDimensions = () => {
            if (containerRef.current) {
                setDimensions({
                    width: containerRef.current.clientWidth,
                    height: window.innerHeight - 200 // dynamic height
                })
            }
        }

        window.addEventListener('resize', updateDimensions)
        updateDimensions()

        return () => window.removeEventListener('resize', updateDimensions)
    }, [])

    return (
        <div className="column column-center" style={{ width: '100%', height: '100%' }}>
            <div ref={containerRef} style={{ width: '100%', height: '100%', position: 'relative' }}>
                {loading && (
                    <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', zIndex: 10 }}>
                        <div className="loading-spinner">Loading Knowledge Graph...</div>
                    </div>
                )}

                {error && (
                    <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', color: 'red', zIndex: 10 }}>
                        {error}
                    </div>
                )}

                {!loading && !error && (
                    <div style={{ border: '1px solid var(--glass-border)', borderRadius: '12px', overflow: 'hidden', background: 'var(--glass-bg)' }}>
                        <ForceGraph2D
                            width={dimensions.width}
                            height={dimensions.height}
                            graphData={data}
                            nodeLabel="id"
                            nodeAutoColorBy="type"
                            linkDirectionalArrowLength={3.5}
                            linkDirectionalArrowRelPos={1}
                            backgroundColor="rgba(0,0,0,0)"
                            linkColor={() => 'rgba(255,255,255,0.2)'}
                            nodeCanvasObject={(node, ctx, globalScale) => {
                                const label = node.id as string;
                                const fontSize = 12 / globalScale;
                                ctx.font = `${fontSize}px Sans-Serif`;
                                const textWidth = ctx.measureText(label).width;
                                const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2); // some padding

                                ctx.fillStyle = 'rgba(0, 0, 0, 0.2)';
                                if (node.x && node.y) {
                                    ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y - bckgDimensions[1] / 2, bckgDimensions[0], bckgDimensions[1]);
                                }

                                ctx.textAlign = 'center';
                                ctx.textBaseline = 'middle';
                                ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
                                if (node.x && node.y) {
                                    ctx.fillText(label, node.x, node.y);
                                }

                                // Draw node circle (if not covered by text or just for emphasis)
                                // ctx.beginPath(); 
                                // ctx.arc(node.x, node.y, 5, 0, 2 * Math.PI, false); 
                                // ctx.fill();
                            }}
                            onNodeClick={node => {
                                // Center/Zoom on node logic could go here
                                console.log('Clicked node:', node)
                            }}
                        />
                    </div>
                )}
            </div>

            <div style={{ padding: '1rem', opacity: 0.7, fontSize: '0.9rem' }}>
                {data.nodes.length} entities · {data.links.length} relationships
            </div>
        </div>
    )
}
