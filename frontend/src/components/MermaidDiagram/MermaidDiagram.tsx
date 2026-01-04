import { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

interface MermaidDiagramProps {
    chart: string;
}

// Initialize mermaid with dark theme
mermaid.initialize({
    startOnLoad: false,
    theme: 'dark',
    themeVariables: {
        primaryColor: '#00d4ff',
        primaryTextColor: '#fff',
        primaryBorderColor: '#00d4ff',
        lineColor: '#00d4ff',
        secondaryColor: '#1a1a2e',
        tertiaryColor: '#16213e',
        background: '#0f0f23',
        mainBkg: '#1a1a2e',
        nodeBorder: '#00d4ff',
        clusterBkg: '#16213e',
        titleColor: '#00d4ff',
        edgeLabelBackground: '#1a1a2e',
    },
    flowchart: {
        curve: 'basis',
        padding: 20,
    },
    securityLevel: 'loose',
});

export function MermaidDiagram({ chart }: MermaidDiagramProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const [svg, setSvg] = useState<string>('');
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const renderDiagram = async () => {
            if (!chart || !containerRef.current) return;

            try {
                // Clean the chart - remove extra whitespace and normalize
                const cleanChart = chart.trim();

                // Generate unique ID
                const id = `mermaid-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

                // Render the diagram
                const { svg: renderedSvg } = await mermaid.render(id, cleanChart);
                setSvg(renderedSvg);
                setError(null);
            } catch (err: any) {
                console.error('Mermaid rendering error:', err);
                setError(err.message || 'Failed to render diagram');
                // Show the raw code as fallback
                setSvg('');
            }
        };

        renderDiagram();
    }, [chart]);

    if (error) {
        return (
            <div className="mermaid-error">
                <p>⚠️ Diagram rendering failed</p>
                <pre>{chart}</pre>
            </div>
        );
    }

    if (!svg) {
        return (
            <div className="mermaid-loading">
                <p>Loading diagram...</p>
            </div>
        );
    }

    return (
        <div
            ref={containerRef}
            className="mermaid-diagram"
            dangerouslySetInnerHTML={{ __html: svg }}
        />
    );
}

export default MermaidDiagram;
