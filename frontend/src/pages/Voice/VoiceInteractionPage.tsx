import { useState } from 'react';
import VoiceChat from '../../components/VoiceChat/VoiceChat';
import type { AgentId } from '../../types';

interface VoiceInteractionPageProps {
  activeAgent: AgentId;
}

export function VoiceInteractionPage({ activeAgent }: VoiceInteractionPageProps) {
  const [status, setStatus] = useState<'connecting' | 'connected' | 'error'>('connecting');
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="voice-interaction-container" style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      gap: '1.5rem',
      padding: '2rem',
    }}>
      <div>
        <h1 style={{ marginBottom: '0.5rem' }}>Voice Interaction</h1>
        <p style={{
          color: 'var(--color-text-dim)',
          fontSize: '0.95rem',
          margin: 0,
        }}>
          Interact with {activeAgent === 'elena' ? 'Elena' : 'Marcus'} using voice. Press and hold to speak.
        </p>
      </div>

      <div style={{
        flex: 1,
        background: 'var(--glass-bg)',
        border: '1px solid var(--glass-border)',
        borderRadius: '12px',
        padding: '2rem',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '400px',
      }}>
        {status === 'error' && error && (
          <div style={{
            color: 'var(--color-error)',
            marginBottom: '1rem',
            textAlign: 'center',
          }}>
            <p>{error}</p>
            <button
              onClick={() => {
                setError(null);
                setStatus('connecting');
              }}
              style={{
                marginTop: '1rem',
                padding: '0.5rem 1rem',
                background: 'var(--color-accent)',
                color: 'var(--color-text)',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
              }}
            >
              Retry
            </button>
          </div>
        )}

        {status !== 'error' && (
          <VoiceChat
            agentId={activeAgent}
            disabled={status !== 'connected'}
            onStatusChange={setStatus}
          />
        )}
      </div>

      <div style={{
        background: 'var(--glass-bg)',
        border: '1px solid var(--glass-border)',
        borderRadius: '8px',
        padding: '1rem',
        fontSize: '0.875rem',
        color: 'var(--color-text-dim)',
      }}>
        <p><strong>Connection Status:</strong> {status}</p>
        <p style={{ margin: '0.5rem 0 0' }}>
          {status === 'connected' ? '🟢 Connected and ready for voice input' : 
           status === 'connecting' ? '🟡 Connecting to voice service...' :
           '🔴 Connection error'}
        </p>
      </div>
    </div>
  );
}
