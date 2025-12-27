import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { listWorkflows, signalWorkflow } from '../../services/api';
import { AGENTS, type AgentId } from '../../types';

interface Workflow {
    workflow_id: string;
    workflow_type: string;
    status: string;
    agent_id?: string;
    started_at: string;
    completed_at?: string | null;
    task_summary: string;
    step_count?: number | null;
    current_step?: string | null;
}

export function ActiveWorkflows() {
    const navigate = useNavigate();
    const [workflows, setWorkflows] = useState<Workflow[]>([]);
    const [loading, setLoading] = useState(true);
    const [signaling, setSignaling] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const fetchWorkflows = async () => {
        try {
            setError(null);
            // Fetch running and waiting workflows
            const runningData = await listWorkflows('running');
            const waitingData = await listWorkflows('waiting');
            setWorkflows([...runningData.workflows, ...waitingData.workflows]);
        } catch (err) {
            console.error('Failed to load workflows:', err);
            setError('Failed to load workflows. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchWorkflows();
        const interval = setInterval(fetchWorkflows, 5000); // Poll every 5s
        return () => clearInterval(interval);
    }, []);

    const handleSignal = async (workflowId: string, signalName: string) => {
        setSignaling(workflowId);
        try {
            await signalWorkflow(workflowId, signalName, { approved: true });
            alert(`Signal '${signalName}' sent to ${workflowId}`);
            fetchWorkflows();
        } catch (err) {
            console.error('Failed to signal workflow:', err);
            alert('Failed to send signal');
        } finally {
            setSignaling(null);
        }
    };

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const getStatusColor = (status: string) => {
        switch (status.toLowerCase()) {
            case 'running':
                return '#4caf50';
            case 'waiting':
                return '#ffc107';
            case 'completed':
                return '#2196f3';
            case 'failed':
                return '#f44336';
            case 'cancelled':
                return '#9e9e9e';
            default:
                return '#757575';
        }
    };

    const getStatusBg = (status: string) => {
        switch (status.toLowerCase()) {
            case 'running':
                return 'rgba(76, 175, 80, 0.1)';
            case 'waiting':
                return 'rgba(255, 193, 7, 0.1)';
            case 'completed':
                return 'rgba(33, 150, 243, 0.1)';
            case 'failed':
                return 'rgba(244, 67, 54, 0.1)';
            case 'cancelled':
                return 'rgba(158, 158, 158, 0.1)';
            default:
                return 'rgba(117, 117, 117, 0.1)';
        }
    };

    const getWorkflowTypeLabel = (type: string) => {
        switch (type) {
            case 'StoryWorkflow':
                return 'Story & Visual Creation';
            case 'AgentWorkflow':
                return 'Agent Execution';
            case 'ApprovalWorkflow':
                return 'Approval Request';
            case 'ConversationWorkflow':
                return 'Conversation';
            default:
                return type;
        }
    };

    const getStepLabel = (step: string | null | undefined) => {
        if (!step) return '—';
        
        const stepMap: Record<string, string> = {
            'generating_story': 'Generating Story (Claude)',
            'generating_diagram': 'Generating Diagram (Gemini)',
            'generating_image': 'Generating Image',
            'saving_artifacts': 'Saving Artifacts',
            'enriching_memory': 'Enriching Memory (Zep)',
        };
        
        return stepMap[step] || step;
    };

    const isStoryWorkflow = (workflow: Workflow) => {
        return workflow.workflow_type === 'StoryWorkflow' || workflow.workflow_id.startsWith('story-');
    };

    const getDelegationChain = (workflow: Workflow) => {
        if (isStoryWorkflow(workflow)) {
            return ['elena', 'sage'];
        }
        return workflow.agent_id ? [workflow.agent_id] : [];
    };

    return (
        <div className="column column-center">
            <div style={{ padding: '2rem', color: 'var(--color-text)', maxWidth: '1200px', width: '100%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <div>
                        <h2>Active Workflows</h2>
                        <p style={{ opacity: 0.7, marginTop: '0.5rem' }}>
                            Currently running and waiting durable execution workflows
                        </p>
                    </div>
                    {workflows.length > 0 && (
                        <div style={{ fontSize: '0.9em', opacity: 0.7 }}>
                            {workflows.length} active workflow{workflows.length !== 1 ? 's' : ''}
                        </div>
                    )}
                </div>

                <div style={{ marginTop: '2rem' }}>
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
                            <p style={{ opacity: 0.7 }}>Loading workflows...</p>
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
                                onClick={fetchWorkflows}
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

                    {!loading && !error && workflows.length === 0 && (
                        <div style={{
                            textAlign: 'center',
                            padding: '3rem',
                            opacity: 0.7
                        }}>
                            <p style={{ fontSize: '1.1em', marginBottom: '0.5rem' }}>No active workflows</p>
                            <p style={{ fontSize: '0.9em' }}>
                                Workflows will appear here when agents delegate tasks or start long-running processes.
                            </p>
                        </div>
                    )}

                    <div style={{ display: 'grid', gap: '1rem' }}>
                        {workflows.map(wf => {
                            const delegationChain = getDelegationChain(wf);
                            const isStory = isStoryWorkflow(wf);
                            
                            return (
                                <div key={wf.workflow_id} style={{
                                    padding: '1.5rem',
                                    background: 'var(--glass-bg)',
                                    border: '1px solid var(--glass-border)',
                                    borderRadius: '8px',
                                    transition: 'transform 0.2s, box-shadow 0.2s'
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
                                    {/* Header */}
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                                        <div style={{ flex: 1 }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                                                <span style={{
                                                    fontSize: '0.75em',
                                                    padding: '4px 8px',
                                                    borderRadius: '4px',
                                                    background: getStatusBg(wf.status),
                                                    color: getStatusColor(wf.status),
                                                    textTransform: 'uppercase',
                                                    fontWeight: '600'
                                                }}>
                                                    {wf.status}
                                                </span>
                                                <span style={{
                                                    fontSize: '0.85em',
                                                    opacity: 0.7,
                                                    padding: '2px 8px',
                                                    background: 'rgba(255,255,255,0.05)',
                                                    borderRadius: '4px'
                                                }}>
                                                    {getWorkflowTypeLabel(wf.workflow_type)}
                                                </span>
                                            </div>
                                            
                                            {/* Delegation Chain for Story Workflows */}
                                            {isStory && delegationChain.length > 1 && (
                                                <div style={{
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    gap: '0.5rem',
                                                    marginBottom: '0.75rem',
                                                    padding: '0.5rem',
                                                    background: 'rgba(255,255,255,0.03)',
                                                    borderRadius: '6px'
                                                }}>
                                                    <span style={{ fontSize: '0.85em', opacity: 0.7 }}>Delegation:</span>
                                                    {delegationChain.map((agentId, idx) => {
                                                        const agent = AGENTS[agentId as AgentId];
                                                        return (
                                                            <div key={agentId} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                                <div style={{
                                                                    width: '28px',
                                                                    height: '28px',
                                                                    borderRadius: '50%',
                                                                    background: agent ? agent.accentColor : 'var(--color-primary)',
                                                                    display: 'flex',
                                                                    alignItems: 'center',
                                                                    justifyContent: 'center',
                                                                    color: '#fff',
                                                                    fontWeight: 'bold',
                                                                    fontSize: '0.75em'
                                                                }}>
                                                                    {agent ? agent.name.charAt(0) : agentId.charAt(0).toUpperCase()}
                                                                </div>
                                                                {idx < delegationChain.length - 1 && (
                                                                    <span style={{ opacity: 0.5, fontSize: '0.9em' }}>→</span>
                                                                )}
                                                            </div>
                                                        );
                                                    })}
                                                    <span style={{ fontSize: '0.85em', opacity: 0.6, marginLeft: '0.5rem' }}>
                                                        (Elena delegates to Sage)
                                                    </span>
                                                </div>
                                            )}
                                            
                                            {/* Single Agent Display */}
                                            {!isStory && wf.agent_id && (
                                                <div style={{
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    gap: '0.5rem',
                                                    marginBottom: '0.75rem'
                                                }}>
                                                    <div style={{
                                                        width: '28px',
                                                        height: '28px',
                                                        borderRadius: '50%',
                                                        background: AGENTS[wf.agent_id as AgentId]?.accentColor || 'var(--color-primary)',
                                                        display: 'flex',
                                                        alignItems: 'center',
                                                        justifyContent: 'center',
                                                        color: '#fff',
                                                        fontWeight: 'bold',
                                                        fontSize: '0.75em'
                                                    }}>
                                                        {AGENTS[wf.agent_id as AgentId]?.name.charAt(0) || wf.agent_id.charAt(0).toUpperCase()}
                                                    </div>
                                                    <span style={{ fontSize: '0.9em', opacity: 0.8 }}>
                                                        {AGENTS[wf.agent_id as AgentId]?.name || wf.agent_id}
                                                    </span>
                                                </div>
                                            )}
                                            
                                            <p style={{ margin: 0, opacity: 0.9, lineHeight: '1.5' }}>
                                                {wf.task_summary}
                                            </p>
                                            
                                            <div style={{ 
                                                display: 'flex', 
                                                gap: '1rem', 
                                                marginTop: '0.75rem',
                                                fontSize: '0.85em',
                                                opacity: 0.7
                                            }}>
                                                {wf.current_step && (
                                                    <span>
                                                        <strong>Step:</strong> {getStepLabel(wf.current_step)}
                                                    </span>
                                                )}
                                                {wf.step_count && (
                                                    <span>
                                                        <strong>Progress:</strong> {wf.step_count} steps
                                                    </span>
                                                )}
                                                <span>
                                                    <strong>Started:</strong> {formatDate(wf.started_at)}
                                                </span>
                                            </div>
                                        </div>
                                        
                                        <div style={{ display: 'flex', gap: '0.5rem', flexDirection: 'column' }}>
                                            <button
                                                onClick={() => navigate(`/workflows/${wf.workflow_id}`)}
                                                style={{
                                                    padding: '0.5rem 1rem',
                                                    background: 'rgba(255,255,255,0.06)',
                                                    color: 'var(--color-text)',
                                                    border: '1px solid var(--glass-border)',
                                                    borderRadius: '4px',
                                                    cursor: 'pointer',
                                                    fontSize: '0.9em',
                                                    transition: 'all 0.2s'
                                                }}
                                                onMouseEnter={(e) => {
                                                    e.currentTarget.style.background = 'rgba(255,255,255,0.1)';
                                                }}
                                                onMouseLeave={(e) => {
                                                    e.currentTarget.style.background = 'rgba(255,255,255,0.06)';
                                                }}
                                            >
                                                View Details
                                            </button>
                                            {wf.status === 'waiting' && (
                                                <button
                                                    onClick={() => handleSignal(wf.workflow_id, 'approve')}
                                                    disabled={signaling === wf.workflow_id}
                                                    style={{
                                                        padding: '0.5rem 1rem',
                                                        background: signaling === wf.workflow_id ? 'rgba(255,255,255,0.1)' : 'var(--color-primary)',
                                                        color: 'white',
                                                        border: 'none',
                                                        borderRadius: '4px',
                                                        cursor: signaling === wf.workflow_id ? 'not-allowed' : 'pointer',
                                                        fontSize: '0.9em',
                                                        opacity: signaling === wf.workflow_id ? 0.6 : 1
                                                    }}
                                                >
                                                    {signaling === wf.workflow_id ? 'Sending...' : 'Approve'}
                                                </button>
                                            )}
                                            <button
                                                onClick={() => handleSignal(wf.workflow_id, 'cancel')}
                                                disabled={signaling === wf.workflow_id}
                                                style={{
                                                    padding: '0.5rem 1rem',
                                                    background: 'rgba(255,50,50,0.1)',
                                                    color: '#ff5252',
                                                    border: '1px solid rgba(255,50,50,0.3)',
                                                    borderRadius: '4px',
                                                    cursor: signaling === wf.workflow_id ? 'not-allowed' : 'pointer',
                                                    fontSize: '0.9em',
                                                    opacity: signaling === wf.workflow_id ? 0.6 : 1
                                                }}
                                            >
                                                Cancel
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>

            <style>{`
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
            `}</style>
        </div>
    );
}
