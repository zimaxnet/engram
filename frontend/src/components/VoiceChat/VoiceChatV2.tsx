/**
 * VoiceChatV2 Component
 * 
 * VoiceLive v2 architecture: Direct browser-to-Azure WebRTC connection
 * with async memory enrichment. Audio flows directly to Azure, transcripts
 * are sent to backend for memory persistence.
 * 
 * This replaces the backend-proxied WebSocket approach from v1.
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { useAzureRealtime, ConnectionStatus } from '../../hooks/useAzureRealtime';
import './VoiceChat.css';

interface VoiceMessage {
    id: string;
    type: 'user' | 'agent';
    text: string;
    agentId?: string;
    timestamp: Date;
}

interface Viseme {
    time_ms: number;
    viseme_id: number;
}

interface VoiceChatV2Props {
    agentId: string;
    sessionId?: string;
    onMessage?: (message: VoiceMessage) => void;
    onVisemes?: (visemes: Viseme[]) => void;
    onStatusChange?: (status: ConnectionStatus) => void;
    disabled?: boolean;
}

export default function VoiceChatV2({
    agentId,
    sessionId: sessionIdProp,
    onMessage,
    onVisemes,
    onStatusChange,
    disabled = false
}: VoiceChatV2Props) {
    const [userTranscription, setUserTranscription] = useState('');
    const [assistantTranscription, setAssistantTranscription] = useState('');
    const [error, setError] = useState<string | null>(null);

    // Use a stable session ID
    const sessionIdRef = useRef(sessionIdProp || `voicelive-v2-${Date.now()}`);

    // Store callbacks in refs to avoid stale closures
    const onMessageRef = useRef(onMessage);
    const onVisemesRef = useRef(onVisemes);
    const onStatusChangeRef = useRef(onStatusChange);

    useEffect(() => {
        onMessageRef.current = onMessage;
        onVisemesRef.current = onVisemes;
        onStatusChangeRef.current = onStatusChange;
    }, [onMessage, onVisemes, onStatusChange]);

    // Transcript handler
    const handleTranscript = useCallback((
        text: string,
        speaker: 'user' | 'assistant',
        isFinal: boolean
    ) => {
        if (speaker === 'user') {
            setUserTranscription(text);
            if (isFinal && text.trim()) {
                onMessageRef.current?.({
                    id: `user-${Date.now()}`,
                    type: 'user',
                    text,
                    timestamp: new Date(),
                });
            }
        } else {
            setAssistantTranscription(text);
            if (isFinal && text.trim()) {
                onMessageRef.current?.({
                    id: `assistant-${Date.now()}`,
                    type: 'agent',
                    agentId,
                    text,
                    timestamp: new Date(),
                });
            }
        }
    }, [agentId]);

    // Status change handler
    const handleStatusChange = useCallback((status: ConnectionStatus) => {
        onStatusChangeRef.current?.(status);
        if (status === 'error') {
            setError('Voice connection failed');
        } else {
            setError(null);
        }
    }, []);

    // Error handler
    const handleError = useCallback((message: string) => {
        setError(message);
    }, []);

    // Initialize the WebRTC hook
    const {
        status,
        isListening,
        isSpeaking,
        connect,
        disconnect,
        cancelResponse,
    } = useAzureRealtime({
        agentId,
        sessionId: sessionIdRef.current,
        onTranscript: handleTranscript,
        onStatusChange: handleStatusChange,
        onError: handleError,
    });

    // Auto-connect on mount
    useEffect(() => {
        connect();
        return () => {
            disconnect();
        };
    }, [connect, disconnect]);

    // Get button state class
    const getButtonClass = () => {
        if (disabled) return 'voice-button disabled';
        if (status === 'connecting') return 'voice-button disabled';
        if (status === 'error') return 'voice-button disabled';
        if (isListening) return 'voice-button listening';
        if (isSpeaking) return 'voice-button speaking';
        return 'voice-button';
    };

    // Get status text
    const getStatusText = () => {
        if (status === 'connecting') return 'Connecting to voice...';
        if (status === 'error') return error || 'Voice connection error';
        if (isListening) return 'Listening...';
        if (isSpeaking) return `${agentId === 'marcus' ? 'Marcus' : 'Elena'} speaking...`;
        if (status === 'connected') return 'Voice ready (WebRTC)';
        return 'Voice not connected';
    };

    return (
        <div className="voice-chat">
            {/* Voice Button */}
            <div className="voice-button-container">
                <button
                    className={getButtonClass()}
                    disabled={disabled || status !== 'connected'}
                    onClick={isSpeaking ? cancelResponse : undefined}
                    title={isSpeaking ? 'Click to cancel' : 'Voice active - speak naturally'}
                >
                    <div className="voice-icon">
                        {isListening && (
                            <svg viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
                                <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
                            </svg>
                        )}
                        {isSpeaking && (
                            <svg viewBox="0 0 24 24" fill="currentColor">
                                <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z" />
                            </svg>
                        )}
                        {!isListening && !isSpeaking && (
                            <svg viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
                                <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
                            </svg>
                        )}
                    </div>
                </button>

                <span className="voice-status">
                    {getStatusText()}
                    {status === 'connected' && (
                        <span className="voice-badge">v2</span>
                    )}
                </span>
            </div>

            {/* Transcription Display */}
            {userTranscription && (
                <div className="transcription">
                    <span className="transcription-label">You said:</span>
                    <span className="transcription-text">{userTranscription}</span>
                </div>
            )}

            {assistantTranscription && (
                <div className="transcription">
                    <span className="transcription-label">
                        {agentId === 'marcus' ? 'Marcus said:' : 'Elena said:'}
                    </span>
                    <span className="transcription-text">{assistantTranscription}</span>
                </div>
            )}

            {/* Error Display */}
            {error && (
                <div className="voice-error">
                    {error}
                </div>
            )}
        </div>
    );
}
