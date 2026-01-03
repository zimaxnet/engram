import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { getStory } from '../../services/api';
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
    // Use 'visual' as default tab if image exists? Or stick to story.
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
            // Fallback for older browsers
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
                // Default to diagram if story is short/empty but diagram exists? No, stick to story.
            } catch (err: any) {
                setError(err.message || 'Failed to load story');
            } finally {
                setLoading(false);
            }
        };

        fetchStory();
    }, [storyId]);

    if (loading) return <div className="story-loading">Loading artifact...</div>;
    if (error) return <div className="story-error">Error: {error}</div>;
    if (!story) return <div className="story-error">Story not found</div>;

    return (
        <div className="story-detail">
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
                <div className="share-row">
                    <button
                        className={`share-button ${copied ? 'copied' : ''}`}
                        onClick={handleShare}
                        title="Copy shareable link"
                    >
                        {copied ? '✅ Copied!' : '🔗 Share'}
                    </button>
                    <span className="share-url">{shareableUrl}</span>
                </div>
            </header>

            <div className="detail-tabs">
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
            </div>

            <div className="detail-content">
                {activeTab === 'story' && (
                    <div className="markdown-content">
                        <ReactMarkdown>{story.story_content}</ReactMarkdown>
                    </div>
                )}

                {activeTab === 'diagram' && story.diagram_spec && (
                    <div className="diagram-view">
                        {/* 
                            In a real implementation, we would use a library like React Flow 
                            or Mermaid to render this spec. For now, we pretty-print the JSON 
                            as a proof of concept.
                         */}
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
                                src={story.image_path}
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
    );
}
