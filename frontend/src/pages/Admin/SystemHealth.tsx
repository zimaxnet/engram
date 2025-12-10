import { useEffect, useState } from 'react';
import { checkHealth, getAuditLogs } from '../../services/api';

export function SystemHealth() {
    const [health, setHealth] = useState<{ status: string; timestamp: string; version: string } | null>(null);
    const [logs, setLogs] = useState<{ id: string; action: string; resource: string; user_id: string }[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [healthData, auditData] = await Promise.all([
                    checkHealth(),
                    getAuditLogs()
                ]);
                setHealth(healthData);
                setLogs(auditData);
            } catch (err) {
                console.error('Failed to load system data:', err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
        const interval = setInterval(() => {
            checkHealth().then(setHealth).catch(console.error);
        }, 30000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="column column-center">
            <div style={{ padding: '2rem', color: 'var(--color-text)', width: '100%', maxWidth: '800px' }}>
                <h2>System Health & Audit</h2>

                <div style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: '1rem',
                    marginTop: '2rem'
                }}>
                    <div style={{
                        padding: '1.5rem',
                        background: 'var(--glass-bg)',
                        border: '1px solid var(--glass-border)',
                        borderRadius: '8px'
                    }}>
                        <h3>Backend Status</h3>
                        {loading ? 'Checking...' : (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '1rem' }}>
                                <div style={{
                                    width: '12px',
                                    height: '12px',
                                    borderRadius: '50%',
                                    background: health?.status === 'ok' ? '#4caf50' : '#ff5252'
                                }}></div>
                                <span style={{ fontSize: '1.2em' }}>
                                    {health?.status === 'ok' ? 'Operational' : 'Issues Detected'}
                                </span>
                            </div>
                        )}
                        <div style={{ marginTop: '1rem', opacity: 0.7, fontSize: '0.9em' }}>
                            Last Checked: {health?.timestamp ? new Date(health.timestamp).toLocaleTimeString() : 'Unknown'} <br />
                            Version: {health?.version || '0.0.0'}
                        </div>
                    </div>

                    <div style={{
                        padding: '1.5rem',
                        background: 'var(--glass-bg)',
                        border: '1px solid var(--glass-border)',
                        borderRadius: '8px'
                    }}>
                        <h3>Recent Activity</h3>
                        <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                            {logs.slice(0, 3).map(log => (
                                <div key={log.id} style={{ fontSize: '0.9em', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '0.5rem' }}>
                                    <span style={{ fontWeight: 'bold' }}>{log.action}</span>
                                    <span style={{ opacity: 0.7 }}> on {log.resource} by {log.user_id}</span>
                                </div>
                            ))}
                            {logs.length === 0 && <span style={{ opacity: 0.5 }}>No recent activity.</span>}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
