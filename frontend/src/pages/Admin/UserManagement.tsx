import { useEffect, useState } from 'react';
import { listUsers } from '../../services/api';

export function UserManagement() {
    const [users, setUsers] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadUsers = async () => {
            try {
                const data = await listUsers();
                setUsers(data);
            } catch (err) {
                console.error('Failed to load users:', err);
            } finally {
                setLoading(false);
            }
        };
        loadUsers();
    }, []);

    return (
        <div className="column column-center">
            <div style={{ padding: '2rem', color: 'var(--color-text)', width: '100%', maxWidth: '800px' }}>
                <h2>User Management</h2>
                <div style={{ marginTop: '2rem' }}>
                    {loading && <p>Loading users...</p>}

                    <table style={{
                        width: '100%',
                        borderCollapse: 'collapse',
                        background: 'var(--glass-bg)',
                        borderRadius: '8px',
                        overflow: 'hidden'
                    }}>
                        <thead style={{ background: 'rgba(255,255,255,0.05)' }}>
                            <tr>
                                <th style={{ padding: '1rem', textAlign: 'left' }}>User ID</th>
                                <th style={{ padding: '1rem', textAlign: 'left' }}>Email</th>
                                <th style={{ padding: '1rem', textAlign: 'left' }}>Role</th>
                                <th style={{ padding: '1rem', textAlign: 'left' }}>Status</th>
                                <th style={{ padding: '1rem', textAlign: 'left' }}>Last Login</th>
                            </tr>
                        </thead>
                        <tbody>
                            {users.map((user, i) => (
                                <tr key={user.user_id} style={{ borderTop: i > 0 ? '1px solid var(--glass-border)' : 'none' }}>
                                    <td style={{ padding: '1rem' }}>{user.user_id}</td>
                                    <td style={{ padding: '1rem' }}>{user.email}</td>
                                    <td style={{ padding: '1rem' }}>
                                        <span style={{
                                            padding: '2px 8px',
                                            borderRadius: '10px',
                                            background: 'rgba(255,255,255,0.1)',
                                            fontSize: '0.85em'
                                        }}>{user.role}</span>
                                    </td>
                                    <td style={{ padding: '1rem' }}>
                                        <span style={{ color: user.active ? '#4caf50' : '#ff5252' }}>
                                            {user.active ? 'Active' : 'Inactive'}
                                        </span>
                                    </td>
                                    <td style={{ padding: '1rem', fontSize: '0.9em', opacity: 0.7 }}>
                                        {new Date(user.last_login).toLocaleString()}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
