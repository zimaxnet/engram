import React, { useState, useEffect, useRef, Component, type ErrorInfo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { getStory, uploadArchitectureImage, API_BASE_URL } from '../../services/api';
import { MermaidDiagram } from '../../components/MermaidDiagram/MermaidDiagram';
import '../../components/MermaidDiagram/MermaidDiagram.css';
import './StoryDetail.css';

interface StoryDetailed {
    story_id: string;
    topic: string;
    story_content: string;
    diagram_spec?: any;
    image_path?: string | null;
    architecture_image_path?: string | null;
    created_at: string;
}

class ErrorBoundary extends Component<{ children: React.ReactNode }, { hasError: boolean; error: Error | null }> {
    constructor(props: { children: React.ReactNode }) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error: Error) {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error("StoryDetail crashed:", error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="story-error-boundary" style={{ padding: '2rem', textAlign: 'center' }}>
                    <h2>⚠️ Something went wrong displaying this story.</h2>
                    <pre style={{ textAlign: 'left', background: '#333', padding: '1rem', overflow: 'auto' }}>
                        {this.state.error?.toString()}
                    </pre>
                </div>
            );
        }
        return this.props.children;
    }
}

export function StoryDetail() {
    const { storyId } = useParams<{ storyId: string }>();
    const navigate = useNavigate();
    const [story, setStory] = useState<StoryDetailed | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'story' | 'diagram' | 'visual'>('story');
    const [copied, setCopied] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [uploadError, setUploadError] = useState<string | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

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

    const getFullImageUrl = (path: string | null | undefined) => {
        if (!path) return '';
        if (path.startsWith('http')) return path;
        return `${API_BASE_URL}${path}`;
    };

    const handleUploadClick = () => {
        fileInputRef.current?.click();
    };

    const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file || !storyId) return;

        // Validate file type
        const allowedTypes = ['image/png', 'image/jpeg', 'image/webp'];
        if (!allowedTypes.includes(file.type)) {
            setUploadError('Please select a PNG, JPG, or WebP image');
            return;
        }

        setUploading(true);
        setUploadError(null);

        try {
            const updatedStory = await uploadArchitectureImage(storyId, file);
            setStory(updatedStory);
        } catch (err: any) {
            setUploadError(err.message || 'Upload failed');
        } finally {
            setUploading(false);
            // Reset file input
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        }
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

    const toggleModal = () => setIsModalOpen(!isModalOpen);

    return (
        <ErrorBoundary>
            <section className="column column-center">
                <div className="story-detail-container">
                    <header className="detail-header">
                        <div className="header-top-row">
                            <button className="back-button" onClick={() => navigate('/stories')}>
                                ← Back
                            </button>
                            <button className="mobile-share-button" onClick={handleShare}>
                                {copied ? '✅' : '🔗'} Share
                            </button>
                        </div>
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
                                📐 Architecture
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
                                {/* Upload button and uploaded image */}
                                <div className="architecture-upload-section">
                                    <input
                                        type="file"
                                        ref={fileInputRef}
                                        onChange={handleFileChange}
                                        accept="image/png,image/jpeg,image/webp"
                                        className="hidden-file-input"
                                        aria-label="Upload architecture diagram image"
                                    />
                                    <button
                                        className={`upload-architecture-btn ${uploading ? 'uploading' : ''}`}
                                        onClick={handleUploadClick}
                                        disabled={uploading}
                                    >
                                        {uploading ? '⏳ Uploading...' : '📤 Upload Architecture Diagram'}
                                    </button>
                                    {uploadError && (
                                        <div className="upload-error">{uploadError}</div>
                                    )}
                                </div>

                                {/* Display uploaded architecture image if available */}
                                {story.architecture_image_path && (
                                    <div className="architecture-image-container">
                                        <img
                                            src={getFullImageUrl(story.architecture_image_path)}
                                            alt={`${story.topic} - Architecture Diagram`}
                                            className="architecture-image"
                                        />
                                    </div>
                                )}

                                <div className="diagram-placeholder">
                                    <h3>Technical Specification</h3>
                                    <pre>{JSON.stringify(story.diagram_spec, null, 2)}</pre>
                                </div>
                            </div>
                        )}

                        {activeTab === 'visual' && (
                            <div className="visual-view">
                                {story.image_path ? (
                                    <div className="visual-image-wrapper" onClick={toggleModal}>
                                        <img
                                            src={getFullImageUrl(story.image_path)}
                                            alt={story.topic}
                                            className="story-image-full clickable"
                                        />
                                        <div className="image-overlay-hint">
                                            <span>🔍 Tap to expand</span>
                                        </div>
                                    </div>
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

            {/* Image Modal */}
            {isModalOpen && story.image_path && (
                <div className="image-modal-overlay" onClick={toggleModal}>
                    <button className="image-modal-close" onClick={toggleModal}>×</button>
                    <div className="image-modal-content" onClick={e => e.stopPropagation()}>
                        <img
                            src={getFullImageUrl(story.image_path)}
                            alt={story.topic}
                        />
                        <div className="image-modal-caption">
                            {story.topic}
                        </div>
                    </div>
                </div>
            )}
        </ErrorBoundary>
    );
}

