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
    created_at: string;
}

export function StoryDetail() {
    const { storyId } = useParams<{ storyId: string }>();
    const navigate = useNavigate();
    const [story, setStory] = useState<StoryDetailed | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'story' | 'diagram'>('story');

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
            </div>
        </div>
    );
}
