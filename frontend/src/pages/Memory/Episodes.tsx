import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { listEpisodes, getEpisode } from '../../services/api';
import { AGENTS, type AgentId } from '../../types';

interface Episode {
    id: string;
    summary: string;
    turn_count: number;
    agent_id: string;
    started_at: string;
    ended_at: string | null;
    topics: string[];
}

const EPISODES_PER_PAGE = 10;

export function Episodes() {
    const navigate = useNavigate();
    const [episodes, setEpisodes] = useState<Episode[]>([]);
    const [allEpisodes, setAllEpisodes] = useState<Episode[]>([]);
    const [loading, setLoading] = useState(true);
    const [loadingTranscript, setLoadingTranscript] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [selectedTranscript, setSelectedTranscript] = useState<{ role: string; content: string }[] | null>(null);
    const [selectedEpisode, setSelectedEpisode] = useState<Episode | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    
    // Filtering and search state
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedAgent, setSelectedAgent] = useState<string>('all');
    const [selectedTopic, setSelectedTopic] = useState<string>('all');
    const [dateFrom, setDateFrom] = useState<string>('');
    const [dateTo, setDateTo] = useState<string>('');
    
    // Pagination state
    const [currentPage, setCurrentPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);

    // Fetch episodes
    useEffect(() => {
        const fetchEpisodes = async () => {
            setLoading(true);
            setError(null);
            try {
                // Fetch all episodes (we'll do client-side filtering for now)
                // In production, you might want server-side filtering
                const data = await listEpisodes(100, 0);
                setAllEpisodes(data.episodes);
                setTotalCount(data.total_count);
            } catch (err) {
                console.error('Failed to load episodes:', err);
                setError('Failed to load episodes. Please try again.');
            } finally {
                setLoading(false);
            }
        };
        fetchEpisodes();
    }, []);

    // Filter and search episodes
    const filteredEpisodes = useMemo(() => {
        let filtered = [...allEpisodes];

        // Text search (summary, topics)
        if (searchQuery) {
            const query = searchQuery.toLowerCase();
            filtered = filtered.filter(ep => 
                ep.summary.toLowerCase().includes(query) ||
                ep.topics.some(topic => topic.toLowerCase().includes(query))
            );
        }

        // Agent filter
        if (selectedAgent !== 'all') {
            filtered = filtered.filter(ep => ep.agent_id === selectedAgent);
        }

        // Topic filter
        if (selectedTopic !== 'all') {
            filtered = filtered.filter(ep => ep.topics.includes(selectedTopic));
        }

        // Date range filter
        if (dateFrom) {
            const fromDate = new Date(dateFrom);
            filtered = filtered.filter(ep => new Date(ep.started_at) >= fromDate);
        }
        if (dateTo) {
            const toDate = new Date(dateTo);
            toDate.setHours(23, 59, 59, 999); // End of day
            filtered = filtered.filter(ep => new Date(ep.started_at) <= toDate);
        }

        // Sort by most recent first
        filtered.sort((a, b) => 
            new Date(b.started_at).getTime() - new Date(a.started_at).getTime()
        );

        return filtered;
    }, [allEpisodes, searchQuery, selectedAgent, selectedTopic, dateFrom, dateTo]);

    // Pagination
    const totalPages = Math.ceil(filteredEpisodes.length / EPISODES_PER_PAGE);
    const paginatedEpisodes = useMemo(() => {
        const start = (currentPage - 1) * EPISODES_PER_PAGE;
        return filteredEpisodes.slice(start, start + EPISODES_PER_PAGE);
    }, [filteredEpisodes, currentPage]);

    // Get unique topics for filter dropdown
    const allTopics = useMemo(() => {
        const topics = new Set<string>();
        allEpisodes.forEach(ep => ep.topics.forEach(t => topics.add(t)));
        return Array.from(topics).sort();
    }, [allEpisodes]);

    // Reset to page 1 when filters change
    useEffect(() => {
        setCurrentPage(1);
    }, [searchQuery, selectedAgent, selectedTopic, dateFrom, dateTo]);

    const handleViewContext = async (id: string) => {
        setLoadingTranscript(true);
        try {
            const episode = allEpisodes.find(e => e.id === id);
            const data = await getEpisode(id);
            setSelectedTranscript(data.transcript);
            setSelectedEpisode(episode || null);
            setIsModalOpen(true);
        } catch (err) {
            console.error('Failed to load context:', err);
            setError('Failed to load episode transcript. Please try again.');
        } finally {
            setLoadingTranscript(false);
        }
    };

    const handleDiscussWithAgent = (episodeId: string, agentId: string) => {
        try {
            sessionStorage.setItem('engram_session_id', episodeId);
            navigate('/', { 
                state: { 
                    sessionId: episodeId,
                    agentId: agentId 
                } 
            });
        } catch (err) {
            console.error('Failed to set session ID:', err);
            setError('Failed to navigate to chat. Please try again.');
        }
    };

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const formatDateRange = (start: string, end: string | null) => {
        const startDate = formatDate(start);
        if (!end) return startDate;
        const endDate = formatDate(end);
        if (startDate.split(',')[0] === endDate.split(',')[0]) {
            // Same day, just show time range
            return `${startDate} - ${endDate.split(',')[1]}`;
        }
        return `${startDate} - ${endDate}`;
    };

    const getAgentDisplayName = (agentId: string) => {
        const agent = AGENTS[agentId as AgentId];
        return agent ? agent.name : agentId;
    };

    const getAgentColor = (agentId: string) => {
        const agent = AGENTS[agentId as AgentId];
        return agent ? agent.accentColor : 'var(--color-primary)';
    };

    const clearFilters = () => {
        setSearchQuery('');
        setSelectedAgent('all');
        setSelectedTopic('all');
        setDateFrom('');
        setDateTo('');
    };

    return (
        <div className="column column-center">
            <div style={{ padding: '2rem', color: 'var(--color-text)', maxWidth: '1200px', width: '100%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <div>
                        <h2>Episodes</h2>
                        <p style={{ opacity: 0.7, marginTop: '0.5rem' }}>
                            Historical conversation episodes and summaries
                        </p>
                    </div>
                    {filteredEpisodes.length > 0 && (
                        <div style={{ fontSize: '0.9em', opacity: 0.7 }}>
                            {filteredEpisodes.length} episode{filteredEpisodes.length !== 1 ? 's' : ''}
                        </div>
                    )}
                </div>

                {/* Filters and Search */}
                <div style={{
                    background: 'var(--glass-bg)',
                    border: '1px solid var(--glass-border)',
                    borderRadius: '8px',
                    padding: '1.5rem',
                    marginBottom: '2rem'
                }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
                        {/* Search */}
                        <div>
                            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9em', opacity: 0.8 }}>
                                Search
                            </label>
                            <input
                                type="text"
                                placeholder="Search summaries or topics..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                style={{
                                    width: '100%',
                                    padding: '0.5rem',
                                    background: 'rgba(255,255,255,0.05)',
                                    border: '1px solid var(--glass-border)',
                                    borderRadius: '4px',
                                    color: 'var(--color-text)',
                                    fontSize: '0.9em'
                                }}
                            />
                        </div>

                        {/* Agent Filter */}
                        <div>
                            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9em', opacity: 0.8 }}>
                                Agent
                            </label>
                            <select
                                value={selectedAgent}
                                onChange={(e) => setSelectedAgent(e.target.value)}
                                style={{
                                    width: '100%',
                                    padding: '0.5rem',
                                    background: 'rgba(255,255,255,0.05)',
                                    border: '1px solid var(--glass-border)',
                                    borderRadius: '4px',
                                    color: 'var(--color-text)',
                                    fontSize: '0.9em',
                                    cursor: 'pointer'
                                }}
                            >
                                <option value="all">All Agents</option>
                                <option value="elena">Elena</option>
                                <option value="marcus">Marcus</option>
                                <option value="sage">Sage</option>
                            </select>
                        </div>

                        {/* Topic Filter */}
                        {allTopics.length > 0 && (
                            <div>
                                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9em', opacity: 0.8 }}>
                                    Topic
                                </label>
                                <select
                                    value={selectedTopic}
                                    onChange={(e) => setSelectedTopic(e.target.value)}
                                    style={{
                                        width: '100%',
                                        padding: '0.5rem',
                                        background: 'rgba(255,255,255,0.05)',
                                        border: '1px solid var(--glass-border)',
                                        borderRadius: '4px',
                                        color: 'var(--color-text)',
                                        fontSize: '0.9em',
                                        cursor: 'pointer'
                                    }}
                                >
                                    <option value="all">All Topics</option>
                                    {allTopics.map(topic => (
                                        <option key={topic} value={topic}>{topic}</option>
                                    ))}
                                </select>
                            </div>
                        )}

                        {/* Date From */}
                        <div>
                            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9em', opacity: 0.8 }}>
                                From Date
                            </label>
                            <input
                                type="date"
                                value={dateFrom}
                                onChange={(e) => setDateFrom(e.target.value)}
                                style={{
                                    width: '100%',
                                    padding: '0.5rem',
                                    background: 'rgba(255,255,255,0.05)',
                                    border: '1px solid var(--glass-border)',
                                    borderRadius: '4px',
                                    color: 'var(--color-text)',
                                    fontSize: '0.9em'
                                }}
                            />
                        </div>

                        {/* Date To */}
                        <div>
                            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9em', opacity: 0.8 }}>
                                To Date
                            </label>
                            <input
                                type="date"
                                value={dateTo}
                                onChange={(e) => setDateTo(e.target.value)}
                                style={{
                                    width: '100%',
                                    padding: '0.5rem',
                                    background: 'rgba(255,255,255,0.05)',
                                    border: '1px solid var(--glass-border)',
                                    borderRadius: '4px',
                                    color: 'var(--color-text)',
                                    fontSize: '0.9em'
                                }}
                            />
                        </div>
                    </div>

                    {/* Clear Filters Button */}
                    {(searchQuery || selectedAgent !== 'all' || selectedTopic !== 'all' || dateFrom || dateTo) && (
                        <button
                            onClick={clearFilters}
                            style={{
                                background: 'transparent',
                                border: '1px solid var(--color-primary)',
                                color: 'var(--color-primary)',
                                padding: '0.5rem 1rem',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontSize: '0.9em'
                            }}
                        >
                            Clear Filters
                        </button>
                    )}
                </div>

                {/* Episodes List */}
                <div className="episodes-list">
                    {loading && (
                        <div style={{ textAlign: 'center', padding: '3rem' }}>
                            <div style={{ 
                                display: 'inline-block',
                                width: '40px',
                                height: '40px',
                                border: '3px solid rgba(255,255,255,0.1)',
                                borderTopColor: 'var(--color-primary)',
                                borderRadius: '50%',
                                animation: 'spin 1s linear infinite',
                                marginBottom: '1rem'
                            }}></div>
                            <p style={{ opacity: 0.7 }}>Loading episodes...</p>
                        </div>
                    )}

                    {error && (
                        <div style={{
                            background: 'rgba(255,0,0,0.1)',
                            border: '1px solid var(--color-accent-pink)',
                            borderRadius: '8px',
                            padding: '1rem',
                            marginBottom: '1rem',
                            color: 'var(--color-accent-pink)'
                        }}>
                            {error}
                            <button
                                onClick={() => window.location.reload()}
                                style={{
                                    marginLeft: '1rem',
                                    background: 'var(--color-accent-pink)',
                                    border: 'none',
                                    color: '#fff',
                                    padding: '0.25rem 0.5rem',
                                    borderRadius: '4px',
                                    cursor: 'pointer',
                                    fontSize: '0.85em'
                                }}
                            >
                                Retry
                            </button>
                        </div>
                    )}

                    {!loading && !error && filteredEpisodes.length === 0 && (
                        <div style={{
                            textAlign: 'center',
                            padding: '3rem',
                            opacity: 0.7
                        }}>
                            <p style={{ fontSize: '1.1em', marginBottom: '0.5rem' }}>No episodes found</p>
                            <p style={{ fontSize: '0.9em' }}>
                                {allEpisodes.length === 0 
                                    ? 'No episodes have been created yet.'
                                    : 'Try adjusting your filters to see more results.'}
                            </p>
                        </div>
                    )}

                    {!loading && !error && paginatedEpisodes.map((episode: Episode) => {
                        const agent = AGENTS[episode.agent_id as AgentId];
                        const agentColor = getAgentColor(episode.agent_id);
                        
                        return (
                            <div key={episode.id} style={{
                                padding: '1.5rem',
                                background: 'var(--glass-bg)',
                                border: '1px solid var(--glass-border)',
                                marginBottom: '1rem',
                                borderRadius: '8px',
                                transition: 'transform 0.2s, box-shadow 0.2s',
                                cursor: 'pointer'
                            }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.transform = 'translateY(-2px)';
                                e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.2)';
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.transform = 'translateY(0)';
                                e.currentTarget.style.boxShadow = 'none';
                            }}
                            >
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                                    <div style={{ flex: 1 }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                                            <div style={{
                                                width: '32px',
                                                height: '32px',
                                                borderRadius: '50%',
                                                background: agentColor,
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                color: '#fff',
                                                fontWeight: 'bold',
                                                fontSize: '0.9em'
                                            }}>
                                                {agent ? agent.name.charAt(0) : episode.agent_id.charAt(0).toUpperCase()}
                                            </div>
                                            <div>
                                                <h4 style={{ margin: 0, fontSize: '1.1em' }}>
                                                    {getAgentDisplayName(episode.agent_id)}
                                                </h4>
                                                <p style={{ margin: 0, fontSize: '0.85em', opacity: 0.7 }}>
                                                    {formatDateRange(episode.started_at, episode.ended_at)}
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                    <div style={{ 
                                        display: 'flex', 
                                        flexDirection: 'column', 
                                        alignItems: 'flex-end',
                                        gap: '0.5rem'
                                    }}>
                                        <span style={{ 
                                            opacity: 0.7, 
                                            fontSize: '0.85em',
                                            background: 'rgba(255,255,255,0.1)',
                                            padding: '0.25rem 0.5rem',
                                            borderRadius: '4px'
                                        }}>
                                            {episode.turn_count} turn{episode.turn_count !== 1 ? 's' : ''}
                                        </span>
                                    </div>
                                </div>

                                <p style={{ 
                                    opacity: 0.9, 
                                    marginBottom: '1rem',
                                    lineHeight: '1.6'
                                }}>
                                    {episode.summary}
                                </p>

                                {episode.topics.length > 0 && (
                                    <div style={{ 
                                        display: 'flex', 
                                        gap: '0.5rem', 
                                        flexWrap: 'wrap',
                                        marginBottom: '1rem'
                                    }}>
                                        {episode.topics.map((t: string) => (
                                            <span key={t} style={{
                                                background: 'rgba(255,255,255,0.1)',
                                                padding: '0.25rem 0.75rem',
                                                borderRadius: '12px',
                                                fontSize: '0.8em',
                                                border: `1px solid ${agentColor}40`
                                            }}>
                                                {t}
                                            </span>
                                        ))}
                                    </div>
                                )}

                                <div style={{ 
                                    display: 'flex', 
                                    gap: '0.75rem',
                                    justifyContent: 'flex-end'
                                }}>
                                    <button
                                        onClick={() => handleViewContext(episode.id)}
                                        style={{
                                            background: 'transparent',
                                            border: `1px solid ${agentColor}`,
                                            color: agentColor,
                                            padding: '0.5rem 1rem',
                                            borderRadius: '4px',
                                            cursor: 'pointer',
                                            fontSize: '0.9em',
                                            transition: 'all 0.2s'
                                        }}
                                        onMouseEnter={(e) => {
                                            e.currentTarget.style.background = `${agentColor}20`;
                                        }}
                                        onMouseLeave={(e) => {
                                            e.currentTarget.style.background = 'transparent';
                                        }}
                                    >
                                        View Context
                                    </button>
                                    <button
                                        onClick={() => handleDiscussWithAgent(episode.id, episode.agent_id)}
                                        style={{
                                            background: agentColor,
                                            border: 'none',
                                            color: '#fff',
                                            padding: '0.5rem 1rem',
                                            borderRadius: '4px',
                                            cursor: 'pointer',
                                            fontSize: '0.9em',
                                            transition: 'opacity 0.2s'
                                        }}
                                        onMouseEnter={(e) => {
                                            e.currentTarget.style.opacity = '0.9';
                                        }}
                                        onMouseLeave={(e) => {
                                            e.currentTarget.style.opacity = '1';
                                        }}
                                    >
                                        Continue Chat
                                    </button>
                                </div>
                            </div>
                        );
                    })}
                </div>

                {/* Pagination */}
                {!loading && !error && totalPages > 1 && (
                    <div style={{
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        gap: '0.5rem',
                        marginTop: '2rem',
                        padding: '1rem'
                    }}>
                        <button
                            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                            disabled={currentPage === 1}
                            style={{
                                padding: '0.5rem 1rem',
                                background: currentPage === 1 ? 'rgba(255,255,255,0.05)' : 'var(--color-primary)',
                                border: 'none',
                                borderRadius: '4px',
                                color: '#fff',
                                cursor: currentPage === 1 ? 'not-allowed' : 'pointer',
                                opacity: currentPage === 1 ? 0.5 : 1
                            }}
                        >
                            Previous
                        </button>
                        
                        <span style={{ 
                            padding: '0.5rem 1rem',
                            opacity: 0.7,
                            fontSize: '0.9em'
                        }}>
                            Page {currentPage} of {totalPages}
                        </span>
                        
                        <button
                            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                            disabled={currentPage === totalPages}
                            style={{
                                padding: '0.5rem 1rem',
                                background: currentPage === totalPages ? 'rgba(255,255,255,0.05)' : 'var(--color-primary)',
                                border: 'none',
                                borderRadius: '4px',
                                color: '#fff',
                                cursor: currentPage === totalPages ? 'not-allowed' : 'pointer',
                                opacity: currentPage === totalPages ? 0.5 : 1
                            }}
                        >
                            Next
                        </button>
                    </div>
                )}
            </div>

            {/* Transcript Modal */}
            {isModalOpen && (
                <div style={{
                    position: 'fixed',
                    top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.8)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    zIndex: 1000
                }} onClick={() => setIsModalOpen(false)}>
                    <div style={{
                        background: '#1a1a1a',
                        border: '1px solid var(--glass-border)',
                        padding: '2rem',
                        borderRadius: '8px',
                        maxWidth: '700px',
                        width: '90%',
                        maxHeight: '80vh',
                        overflowY: 'auto',
                        boxShadow: '0 8px 32px rgba(0,0,0,0.5)'
                    }} onClick={e => e.stopPropagation()}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                            <div>
                                <h3 style={{ margin: 0 }}>Episode Transcript</h3>
                                {selectedEpisode && (
                                    <p style={{ margin: '0.5rem 0 0 0', opacity: 0.7, fontSize: '0.9em' }}>
                                        {getAgentDisplayName(selectedEpisode.agent_id)} • {selectedEpisode.turn_count} turns
                                    </p>
                                )}
                            </div>
                            <button 
                                onClick={() => setIsModalOpen(false)} 
                                style={{ 
                                    background: 'none', 
                                    border: 'none', 
                                    color: '#fff', 
                                    cursor: 'pointer', 
                                    fontSize: '1.5em',
                                    padding: '0.25rem 0.5rem',
                                    borderRadius: '4px',
                                    transition: 'background 0.2s'
                                }}
                                onMouseEnter={(e) => {
                                    e.currentTarget.style.background = 'rgba(255,255,255,0.1)';
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.background = 'none';
                                }}
                            >
                                ×
                            </button>
                        </div>
                        
                        {loadingTranscript ? (
                            <div style={{ textAlign: 'center', padding: '2rem' }}>
                                <div style={{ 
                                    display: 'inline-block',
                                    width: '32px',
                                    height: '32px',
                                    border: '3px solid rgba(255,255,255,0.1)',
                                    borderTopColor: 'var(--color-primary)',
                                    borderRadius: '50%',
                                    animation: 'spin 1s linear infinite',
                                    marginBottom: '1rem'
                                }}></div>
                                <p style={{ opacity: 0.7 }}>Loading transcript...</p>
                            </div>
                        ) : (
                            <div className="transcript-body">
                                {selectedTranscript && selectedTranscript.length === 0 ? (
                                    <p style={{ opacity: 0.6, textAlign: 'center', padding: '2rem' }}>
                                        No detailed transcript available for this episode.
                                    </p>
                                ) : (
                                    selectedTranscript?.map((msg: { role: string; content: string }, i: number) => (
                                        <div key={i} style={{ 
                                            marginBottom: '1.5rem', 
                                            paddingBottom: '1.5rem', 
                                            borderBottom: '1px solid rgba(255,255,255,0.1)'
                                        }}>
                                            <div style={{
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: '0.5rem',
                                                marginBottom: '0.5rem'
                                            }}>
                                                <div style={{
                                                    width: '24px',
                                                    height: '24px',
                                                    borderRadius: '50%',
                                                    background: msg.role === 'user' 
                                                        ? 'var(--color-accent-pink)' 
                                                        : 'var(--color-accent-cyan)',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    justifyContent: 'center',
                                                    color: '#fff',
                                                    fontWeight: 'bold',
                                                    fontSize: '0.75em'
                                                }}>
                                                    {msg.role === 'user' ? 'U' : 'A'}
                                                </div>
                                                <span style={{
                                                    fontWeight: 'bold',
                                                    color: msg.role === 'user' 
                                                        ? 'var(--color-accent-pink)' 
                                                        : 'var(--color-accent-cyan)',
                                                    textTransform: 'capitalize',
                                                    fontSize: '0.9em'
                                                }}>
                                                    {msg.role === 'user' ? 'You' : selectedEpisode?.agent_id || 'Agent'}
                                                </span>
                                            </div>
                                            <div style={{ 
                                                lineHeight: '1.6',
                                                paddingLeft: '2rem',
                                                whiteSpace: 'pre-wrap'
                                            }}>
                                                {msg.content}
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        )}
                        
                        {selectedEpisode && (
                            <div style={{ 
                                marginTop: '1.5rem', 
                                paddingTop: '1.5rem',
                                borderTop: '1px solid rgba(255,255,255,0.1)',
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center'
                            }}>
                                <div style={{ fontSize: '0.9em', opacity: 0.7 }}>
                                    {selectedEpisode.topics.length > 0 && (
                                        <div style={{ marginBottom: '0.5rem' }}>
                                            <strong>Topics:</strong> {selectedEpisode.topics.join(', ')}
                                        </div>
                                    )}
                                    <div>
                                        <strong>Date:</strong> {formatDateRange(selectedEpisode.started_at, selectedEpisode.ended_at)}
                                    </div>
                                </div>
                                <button style={{
                                    background: getAgentColor(selectedEpisode.agent_id),
                                    border: 'none',
                                    color: '#fff',
                                    padding: '0.75rem 1.5rem',
                                    borderRadius: '4px',
                                    cursor: 'pointer',
                                    fontSize: '0.95em',
                                    fontWeight: '500',
                                    transition: 'opacity 0.2s'
                                }}
                                onClick={() => {
                                    if (selectedEpisode) {
                                        handleDiscussWithAgent(selectedEpisode.id, selectedEpisode.agent_id);
                                        setIsModalOpen(false);
                                    }
                                }}
                                onMouseEnter={(e) => {
                                    e.currentTarget.style.opacity = '0.9';
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.opacity = '1';
                                }}
                                >
                                    Continue with {getAgentDisplayName(selectedEpisode.agent_id)}
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            )}

            <style>{`
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
            `}</style>
        </div>
    );
}
