import { useEffect, useState } from 'react';
import { getSystemSettings, updateSystemSettings } from '../../services/api';

export function GeneralSettings() {
    const [settings, setSettings] = useState<Record<string, unknown>>({});
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        const loadSettings = async () => {
            try {
                const data = await getSystemSettings();
                setSettings(data);
            } catch (err) {
                console.error('Failed to load settings:', err);
            } finally {
                setLoading(false);
            }
        };
        loadSettings();
    }, []);

    const handleSave = async () => {
        setSaving(true);
        try {
            await updateSystemSettings(settings);
            alert('Settings saved!');
        } catch (err) {
            console.error('Failed to save settings:', err);
            alert('Failed to save.');
        } finally {
            setSaving(false);
        }
    };

    if (loading) return <div className="column column-center">Loading settings...</div>;

    return (
        <div className="column column-center">
            <div style={{ padding: '2rem', maxWidth: '600px', width: '100%', color: 'var(--color-text)' }}>
                <h2>General Settings</h2>
                <div style={{
                    marginTop: '2rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '1.5rem',
                    background: 'var(--glass-bg)',
                    padding: '2rem',
                    borderRadius: '8px',
                    border: '1px solid var(--glass-border)'
                }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                        <label>Application Name</label>
                        <input
                            type="text"
                            value={(settings['LOG_LEVEL'] as string) || ''}
                            onChange={(e) => setSettings({ ...settings, LOG_LEVEL: e.target.value })}
                            style={{ padding: '0.5rem', borderRadius: '4px', border: '1px solid #ccc' }}
                        />
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                        <label>Maintenance Mode</label>
                        <input
                            type="checkbox"
                            checked={(settings['ENABLE_AUDIT'] as boolean) || false}
                            onChange={(e) => setSettings({ ...settings, ENABLE_AUDIT: e.target.checked })}
                        />
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                        <label>Default Agent</label>
                        <input
                            type="text"
                            value={settings.default_agent || ''}
                            onChange={e => setSettings({ ...settings, default_agent: e.target.value })}
                            style={{ padding: '0.5rem', borderRadius: '4px', border: '1px solid #ccc' }}
                        />
                    </div>

                    <button
                        onClick={handleSave}
                        disabled={saving}
                        style={{
                            marginTop: '1rem',
                            padding: '0.75rem',
                            background: 'var(--color-primary)',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            opacity: saving ? 0.7 : 1
                        }}
                    >
                        {saving ? 'Saving...' : 'Save Configuration'}
                    </button>
                </div>
            </div>
        </div>
    );
}
