/**
 * useAzureRealtime Hook
 * 
 * Provides direct browser-to-Azure WebRTC connection for real-time voice.
 * This is VoiceLive v2 architecture — audio flows directly to Azure,
 * memory enrichment happens asynchronously via text transcripts.
 */

import { useState, useRef, useCallback, useEffect } from 'react';

export interface RealtimeConfig {
    agentId: string;
    sessionId?: string;
    onTranscript?: (text: string, speaker: 'user' | 'assistant', isFinal: boolean) => void;
    onStatusChange?: (status: ConnectionStatus) => void;
    onError?: (error: string) => void;
}

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

interface EphemeralTokenResponse {
    token: string;
    endpoint: string;
    expiresAt?: string;
}

interface RealtimeEvent {
    type: string;
    [key: string]: unknown;
}

export function useAzureRealtime(config: RealtimeConfig) {
    const [status, setStatus] = useState<ConnectionStatus>('disconnected');
    const [isListening, setIsListening] = useState(false);
    const [isSpeaking, setIsSpeaking] = useState(false);

    const peerConnectionRef = useRef<RTCPeerConnection | null>(null);
    const dataChannelRef = useRef<RTCDataChannel | null>(null);
    const audioElementRef = useRef<HTMLAudioElement | null>(null);
    const mediaStreamRef = useRef<MediaStream | null>(null);

    const configRef = useRef(config);
    useEffect(() => {
        configRef.current = config;
    }, [config]);

    // Fetch ephemeral token from backend
    const fetchToken = useCallback(async (): Promise<EphemeralTokenResponse> => {
        const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8082';
        const response = await fetch(`${baseUrl}/api/v1/voice/realtime/token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                agent_id: configRef.current.agentId,
                session_id: configRef.current.sessionId,
            }),
        });

        if (!response.ok) {
            throw new Error(`Token request failed: ${response.status}`);
        }

        return response.json();
    }, []);

    // Send transcript to memory enrichment (fire-and-forget)
    const enrichMemory = useCallback(async (text: string, speaker: 'user' | 'assistant') => {
        try {
            const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8082';
            await fetch(`${baseUrl}/api/v1/memory/enrich`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text,
                    session_id: configRef.current.sessionId,
                    speaker,
                    agent_id: configRef.current.agentId,
                    channel: 'voice',
                }),
            });
        } catch (e) {
            // Fire-and-forget — log but don't fail
            console.warn('Memory enrichment failed (non-blocking):', e);
        }
    }, []);

    // Handle incoming events from Azure
    const handleRealtimeEvent = useCallback((event: RealtimeEvent) => {
        switch (event.type) {
            case 'conversation.item.input_audio_transcription.completed': {
                const text = (event.transcript as string) || '';
                configRef.current.onTranscript?.(text, 'user', true);
                // Async memory enrichment
                enrichMemory(text, 'user');
                break;
            }

            case 'response.audio_transcript.delta': {
                const text = (event.delta as string) || '';
                configRef.current.onTranscript?.(text, 'assistant', false);
                break;
            }

            case 'response.audio_transcript.done': {
                const text = (event.transcript as string) || '';
                configRef.current.onTranscript?.(text, 'assistant', true);
                // Async memory enrichment
                enrichMemory(text, 'assistant');
                setIsSpeaking(false);
                break;
            }

            case 'response.audio.delta': {
                setIsSpeaking(true);
                break;
            }

            case 'response.done': {
                setIsSpeaking(false);
                break;
            }

            case 'input_audio_buffer.speech_started': {
                setIsListening(true);
                break;
            }

            case 'input_audio_buffer.speech_stopped': {
                setIsListening(false);
                break;
            }

            case 'error': {
                const message = (event.error as { message?: string })?.message || 'Unknown error';
                configRef.current.onError?.(message);
                break;
            }
        }
    }, [enrichMemory]);

    // Connect to Azure Realtime via WebRTC
    const connect = useCallback(async () => {
        try {
            setStatus('connecting');
            configRef.current.onStatusChange?.('connecting');

            // Get ephemeral token from backend
            const { token, endpoint } = await fetchToken();

            // Create peer connection
            const pc = new RTCPeerConnection();
            peerConnectionRef.current = pc;

            // Set up audio output
            const audioEl = document.createElement('audio');
            audioEl.autoplay = true;
            audioElementRef.current = audioEl;

            pc.ontrack = (event) => {
                if (event.streams.length > 0) {
                    audioEl.srcObject = event.streams[0];
                }
            };

            // Request microphone access
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaStreamRef.current = stream;
            const audioTrack = stream.getAudioTracks()[0];
            pc.addTrack(audioTrack);

            // Create data channel for events
            const dc = pc.createDataChannel('realtime-channel');
            dataChannelRef.current = dc;

            dc.onopen = () => {
                setStatus('connected');
                configRef.current.onStatusChange?.('connected');
            };

            dc.onmessage = (event) => {
                try {
                    const realtimeEvent = JSON.parse(event.data) as RealtimeEvent;
                    handleRealtimeEvent(realtimeEvent);
                } catch (e) {
                    console.error('Failed to parse realtime event:', e);
                }
            };

            dc.onclose = () => {
                setStatus('disconnected');
                configRef.current.onStatusChange?.('disconnected');
            };

            // Create and send offer
            const offer = await pc.createOffer();
            await pc.setLocalDescription(offer);

            const webrtcUrl = `${endpoint}/openai/v1/realtime/calls?webrtcfilter=on`;
            const sdpResponse = await fetch(webrtcUrl, {
                method: 'POST',
                body: offer.sdp,
                headers: {
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'application/sdp',
                },
            });

            if (!sdpResponse.ok) {
                throw new Error(`SDP exchange failed: ${sdpResponse.status}`);
            }

            const answerSdp = await sdpResponse.text();
            await pc.setRemoteDescription({ type: 'answer', sdp: answerSdp });

            // Monitor connection state
            pc.onconnectionstatechange = () => {
                if (pc.connectionState === 'failed' || pc.connectionState === 'disconnected') {
                    setStatus('error');
                    configRef.current.onStatusChange?.('error');
                }
            };

        } catch (error) {
            console.error('Realtime connection failed:', error);
            setStatus('error');
            configRef.current.onStatusChange?.('error');
            configRef.current.onError?.(error instanceof Error ? error.message : 'Connection failed');
        }
    }, [fetchToken, handleRealtimeEvent]);

    // Disconnect from Azure
    const disconnect = useCallback(() => {
        if (dataChannelRef.current) {
            dataChannelRef.current.close();
            dataChannelRef.current = null;
        }
        if (peerConnectionRef.current) {
            peerConnectionRef.current.close();
            peerConnectionRef.current = null;
        }
        if (mediaStreamRef.current) {
            mediaStreamRef.current.getTracks().forEach(t => t.stop());
            mediaStreamRef.current = null;
        }
        if (audioElementRef.current) {
            audioElementRef.current.srcObject = null;
            audioElementRef.current = null;
        }
        setStatus('disconnected');
        setIsListening(false);
        setIsSpeaking(false);
    }, []);

    // Send text message (for testing/debugging)
    const sendText = useCallback((text: string) => {
        if (!dataChannelRef.current || dataChannelRef.current.readyState !== 'open') {
            console.warn('Data channel not open');
            return;
        }

        const event = {
            type: 'conversation.item.create',
            item: {
                type: 'message',
                role: 'user',
                content: [{ type: 'input_text', text }],
            },
        };
        dataChannelRef.current.send(JSON.stringify(event));
        dataChannelRef.current.send(JSON.stringify({ type: 'response.create' }));
    }, []);

    // Cancel current response
    const cancelResponse = useCallback(() => {
        if (dataChannelRef.current?.readyState === 'open') {
            dataChannelRef.current.send(JSON.stringify({ type: 'response.cancel' }));
        }
    }, []);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            disconnect();
        };
    }, [disconnect]);

    return {
        status,
        isListening,
        isSpeaking,
        connect,
        disconnect,
        sendText,
        cancelResponse,
    };
}
