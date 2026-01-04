import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { getStory, API_BASE_URL } from '../../services/api';
import { MermaidDiagram } from '../../components/MermaidDiagram/MermaidDiagram';
import '../../components/MermaidDiagram/MermaidDiagram.css';
import './StoryDetail.css';

interface StoryDetailed {
    story_id: string;
    topic: string;
    story_content: string;
    diagram_spec?: any;
    image_path?: string;
    created_at: string;
}

export function StoryDetail() {
    const { storyId } = useParams<{ storyId: string }>();
    const navigate = useNavigate();
    const [story, setStory] = useState<StoryDetailed | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'story' | 'diagram' | 'visual'>('story');
    const [copied, setCopied] = useState(false);

    // Generate shareable URL
    const shareableUrl = `https://engram.work/stories/${storyId}`;

    const handleShare = async () => {
        try {
            await navigator.clipboard.writeText(shareableUrl);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            const textArea = document.createElement('textarea');
            textArea.value = shareableUrl;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    useEffect(() => {
        if (!storyId) return;

        const fetchStory = async () => {
            try {
                const data = await getStory(storyId);
                setStory(data);
            } catch (err: any) {
                setError(err.message || 'Failed to load story');
            } finally {
                setLoading(false);
            }
        };

        fetchStory();
    }, [storyId]);

    const getFullImageUrl = (path: string) => {
        if (!path) return '';
        if (path.startsWith('http')) return path;
        return `${API_BASE_URL}${path}`;
    };

    if (loading) return (
        <section className="column column-center">
            <div className="story-loading">Loading artifact...</div>
        </section>
    );

    if (error) return (
        <section className="column column-center">
            <div className="story-error">Error: {error}</div>
        </section>
    );

    if (!story) return (
        <section className="column column-center">
            <div className="story-error">Story not found</div>
        </section>
    );

    return (
        <>
            <section className="column column-center">
                <div className="story-detail-container">
                    <header className="detail-header">
                        <button className="back-button" onClick={() => navigate('/stories')}>
                            ← Back to Artifacts
                        </button>
                        <div className="title-row">
                            <h1>{story.topic}</h1>
                            <span className="detail-date">
                                {new Date(story.created_at).toLocaleString()}
                            </span>
                        </div>
                    </header>

                    <nav className="detail-tabs">
                        <button
                            className={`tab-button ${activeTab === 'story' ? 'active' : ''}`}
                            onClick={() => setActiveTab('story')}
                        >
                            📜 Narrative
                        </button>
                        {story.diagram_spec && (
                            <button
                                className={`tab-button ${activeTab === 'diagram' ? 'active' : ''}`}
                                onClick={() => setActiveTab('diagram')}
                            >
                                📐 Architecture Diagram
                            </button>
                        )}
                        <button
                            className={`tab-button ${activeTab === 'visual' ? 'active' : ''}`}
                            onClick={() => setActiveTab('visual')}
                        >
                            🎨 Visual
                        </button>
                    </nav>

                    <div className="story-content-area">
                        {activeTab === 'story' && (
                            <div className="markdown-content">
                                <ReactMarkdown
                                    components={{
                                        code({ node, className, children, ...props }) {
                                            const match = /language-(\w+)/.exec(className || '');
                                            const language = match ? match[1] : '';

                                            // Render Mermaid diagrams
                                            if (language === 'mermaid') {
                                                const code = String(children).replace(/\n$/, '');
                                                return <MermaidDiagram chart={code} />;
                                            }

                                            // Default code block rendering
                                            return (
                                                <code className={className} {...props}>
                                                    {children}
                                                </code>
                                            );
                                        }
                                    }}
                                >
                                    {story.story_content}
                                </ReactMarkdown>
                            </div>
                        )}

                        {activeTab === 'diagram' && story.diagram_spec && (
                            <div className="diagram-view">
                                <div className="diagram-placeholder">
                                    <h3>Technical Specification</h3>
                                    <pre>{JSON.stringify(story.diagram_spec, null, 2)}</pre>
                                </div>
                            </div>
                        )}

                        {activeTab === 'visual' && (
                            <div className="visual-view">
                                {story.image_path ? (
                                    <img
                                        src={getFullImageUrl(story.image_path)}
                                        alt={story.topic}
                                        className="story-image-full"
                                    />
                                ) : (
                                    <div className="no-visual">
                                        <p>No visual generated for this story.</p>
                                        <p><i>Ask Sage to "create a visual" for this topic.</i></p>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </section>

            <aside className="column column-right">
                <div className="story-sidebar-info">
                    <h3>Artifact Details</h3>
                    <div className="info-item">
                        <label>Story ID</label>
                        <span>{story.story_id}</span>
                    </div>
                    <div className="info-item">
                        <label>Created</label>
                        <span>{new Date(story.created_at).toLocaleDateString()}</span>
                    </div>

                    <div className="share-section">
                        <h4>Share</h4>
                        <div className="share-row">
                            <button
                                className={`share-button ${copied ? 'copied' : ''}`}
                                onClick={handleShare}
                            >
                                {copied ? '✅ Link Copied' : '🔗 Copy Share Link'}
                            </button>
                        </div>
                        <div className="share-url-preview">{shareableUrl}</div>
                    </div>

                    <div className="sidebar-agent-info">
                        <div className="agent-badge">
                            <span className="agent-icon">🧠</span>
                            <div>
                                <strong>Sage Meridian</strong>
                                <p>Senior Staff Architect</p>
                            </div>
                        </div>
                    </div>
                </div>
            </aside>
        </>
    );
}
