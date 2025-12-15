import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { listWorkflows, signalWorkflow } from '../../services/api';

interface Workflow {
    workflow_id: string;
    workflow_type: string;
    status: string;
    agent_id?: string;
    started_at: string;
    task_summary: string;
    step_count?: number | null;
    current_step?: string | null;
}

export function ActiveWorkflows() {
    const navigate = useNavigate();
    const [workflows, setWorkflows] = useState<Workflow[]>([]);
    const [loading, setLoading] = useState(true);
    const [signaling, setSignaling] = useState<string | null>(null);

    const fetchWorkflows = async () => {
        try {
            const data = await listWorkflows('running');
            // Also include 'waiting' for active view
            const waitingData = await listWorkflows('waiting');
            setWorkflows([...data.workflows, ...waitingData.workflows]);
        } catch (err) {
            console.error('Failed to load workflows:', err);
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

    return (
        <div className="column column-center">
            <div style={{ padding: '2rem', color: 'var(--color-text)' }}>
                <h2>Active Workflows</h2>
                <p>Currently running and waiting agent workflows.</p>

                <div style={{ marginTop: '2rem' }}>
                    {loading && <p>Loading active workflows...</p>}

                    {!loading && workflows.length === 0 && (
                        <p style={{ opacity: 0.7 }}>No active workflows.</p>
                    )}

                    <div style={{ display: 'grid', gap: '1rem' }}>
                        {workflows.map(wf => (
                            <div key={wf.workflow_id} style={{
                                padding: '1rem',
                                background: 'var(--glass-bg)',
                                border: '1px solid var(--glass-border)',
                                borderRadius: '8px',
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center'
                            }}>
                                <div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                                        <h4 style={{ margin: 0 }}>{wf.agent_id ?? 'system'}</h4>
                                        <span style={{
                                            fontSize: '0.75em',
                                            padding: '2px 6px',
                                            borderRadius: '4px',
                                            background: wf.status === 'running' ? 'rgba(0,255,100,0.1)' : 'rgba(255,200,0,0.1)',
                                            color: wf.status === 'running' ? '#4caf50' : '#ffc107',
                                            textTransform: 'uppercase'
                                        }}>{wf.status}</span>
                                    </div>
                                    <p style={{ margin: 0, opacity: 0.9 }}>{wf.task_summary}</p>
                                    <p style={{ fontSize: '0.8em', opacity: 0.6, marginTop: '0.25rem' }}>
                                        Step: {wf.current_step ?? '—'} ({wf.step_count ?? '—'} steps)
                                    </p>
                                </div>
                                <div style={{ display: 'flex', gap: '0.5rem' }}>
                                    <button
                                        onClick={() => navigate(`/workflows/${wf.workflow_id}`)}
                                        style={{
                                            padding: '0.5rem 1rem',
                                            background: 'rgba(255,255,255,0.06)',
                                            color: 'var(--color-text)',
                                            border: '1px solid var(--glass-border)',
                                            borderRadius: '4px',
                                            cursor: 'pointer'
                                        }}
                                    >
                                        Details
                                    </button>
                                    {wf.status === 'waiting' && (
                                        <button
                                            onClick={() => handleSignal(wf.workflow_id, 'approve')}
                                            disabled={signaling === wf.workflow_id}
                                            style={{
                                                padding: '0.5rem 1rem',
                                                background: 'var(--color-primary)',
                                                color: 'white',
                                                border: 'none',
                                                borderRadius: '4px',
                                                cursor: 'pointer'
                                            }}
                                        >
                                            Approve
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
                                            cursor: 'pointer'
                                        }}
                                    >
                                        Cancel
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
