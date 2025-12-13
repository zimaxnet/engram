import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { listWorkflows } from '../../services/api';

interface Workflow {
    workflow_id: string;
    workflow_type: string;
    status: string;
    agent_id: string;
    started_at: string;
    completed_at?: string;
    task_summary: string;
    step_count: number;
}

export function WorkflowHistory() {
    const navigate = useNavigate();
    const [workflows, setWorkflows] = useState<Workflow[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                const data = await listWorkflows('completed');
                // Also include failed/cancelled if API supports multi-status or fetch separately
                // For now just completed
                setWorkflows(data.workflows);
            } catch (err) {
                console.error('Failed to load history:', err);
            } finally {
                setLoading(false);
            }
        };
        fetchHistory();
    }, []);

    return (
        <div className="column column-center">
            <div style={{ padding: '2rem', color: 'var(--color-text)' }}>
                <h2>Workflow History</h2>
                <p>Past agent executions and outcomes.</p>

                <div style={{ marginTop: '2rem' }}>
                    {loading && <p>Loading history...</p>}

                    {!loading && workflows.length === 0 && (
                        <p style={{ opacity: 0.7 }}>No completed workflows.</p>
                    )}

                    <div style={{ display: 'grid', gap: '1rem' }}>
                        {workflows.map(wf => (
                            <div key={wf.workflow_id} style={{
                                padding: '1rem',
                                background: 'var(--glass-bg)',
                                border: '1px solid var(--glass-border)',
                                borderRadius: '8px'
                            }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        <h4 style={{ margin: 0 }}>{wf.agent_id}</h4>
                                        <span style={{
                                            fontSize: '0.75em',
                                            padding: '2px 6px',
                                            borderRadius: '4px',
                                            background: 'rgba(255,255,255,0.1)',
                                            opacity: 0.7
                                        }}>{new Date(wf.completed_at || wf.started_at).toLocaleDateString()}</span>
                                    </div>
                                    <span style={{
                                        fontSize: '0.75em',
                                        padding: '2px 6px',
                                        borderRadius: '4px',
                                        background: 'rgba(100,100,255,0.1)',
                                        color: '#a0a0ff',
                                        textTransform: 'uppercase'
                                    }}>{wf.status}</span>
                                </div>
                                <p style={{ margin: 0, opacity: 0.9 }}>{wf.task_summary}</p>
                                <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem' }}>
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
                                </div>
                                <div style={{ marginTop: '0.5rem', fontSize: '0.8em', opacity: 0.5 }}>
                                    Duration: {wf.completed_at ?
                                        Math.round((new Date(wf.completed_at).getTime() - new Date(wf.started_at).getTime()) / 1000 / 60) + ' min'
                                        : 'Unknown'}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
