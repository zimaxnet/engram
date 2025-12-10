export function SignalsDelegate() {
    return (
        <div className="column column-center">
            <div style={{ padding: '2rem', color: 'var(--color-text)' }}>
                <h2>Signals Control</h2>
                <p>Send manual signals to specific workflow IDs (Debug/Admin).</p>
                <div style={{
                    marginTop: '2rem',
                    padding: '2rem',
                    background: 'var(--glass-bg)',
                    border: '1px solid var(--glass-border)',
                    borderRadius: '8px',
                    textAlign: 'center',
                    opacity: 0.7
                }}>
                    Select 'Active Workflows' to interact with running agents.
                    <br /><br />
                    (This standalone view is reserved for advanced signal injection)
                </div>
            </div>
        </div>
    );
}
