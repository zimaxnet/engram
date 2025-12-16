/**
 * VoiceChat Component
 * 
 * Provides voice interaction with agents:
 * - Push-to-talk voice input
 * - Real-time transcription
 * - Voice output with avatar lip-sync
 */

import { useState, useRef, useCallback, useEffect } from 'react';
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

type IncomingMessage =
  | { type: 'transcription'; status: 'listening' | 'processing' | 'complete' | 'error'; text?: string }
  | { type: 'audio'; data: string; format?: string }
  | { type: 'agent_switched'; agent_id: string }
  | { type: 'error'; message: string };

interface VoiceChatProps {
  agentId: string;
  onMessage?: (message: VoiceMessage) => void;
  onVisemes?: (visemes: Viseme[]) => void;
  onStatusChange?: (status: 'connecting' | 'connected' | 'error') => void;
  disabled?: boolean;
}

export default function VoiceChat({
  agentId,
  onMessage,
  onVisemes,
  onStatusChange,
  disabled = false
}: VoiceChatProps) {
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcription, setTranscription] = useState('');
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'error'>('connecting');
  const [error, setError] = useState<string | null>(null);
  const [audioLevel, setAudioLevel] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const animationFrameRef = useRef<number>(0);
  const streamRef = useRef<MediaStream | null>(null);
  const onStatusChangeRef = useRef(onStatusChange);

  // Store callbacks in refs to avoid stale closures
  const onMessageRef = useRef(onMessage);
  const onVisemesRef = useRef(onVisemes);

  useEffect(() => {
    onMessageRef.current = onMessage;
    onVisemesRef.current = onVisemes;
    onStatusChangeRef.current = onStatusChange;
  }, [onMessage, onVisemes, onStatusChange]);

  // Play audio and trigger visemes
  const playAudio = useCallback(async (
    audioBase64: string,
    format: string,
    visemes: Viseme[]
  ) => {
    try {
      // Decode audio
      const audioData = atob(audioBase64);
      const audioArray = new Uint8Array(audioData.length);
      for (let i = 0; i < audioData.length; i++) {
        audioArray[i] = audioData.charCodeAt(i);
      }

      const blob = new Blob([audioArray], { type: format });
      const url = URL.createObjectURL(blob);

      // Play audio
      if (audioRef.current) {
        audioRef.current.src = url;
        audioRef.current.play();

        // Trigger visemes callback
        if (onVisemesRef.current && visemes.length > 0) {
          onVisemesRef.current(visemes);
        }
      }
    } catch (e) {
      console.error('Failed to play audio:', e);
    }
  }, []);

  // Handle incoming WebSocket messages
  const handleWebSocketMessage = useCallback(
    (data: IncomingMessage) => {
      switch (data.type) {
        case 'transcription':
          setTranscription(data.text || '');
          setIsProcessing(data.status === 'processing');
          if (data.status === 'complete' && data.text) {
            onMessageRef.current?.({
              id: `user-${Date.now()}`,
              type: 'user',
              text: data.text,
              timestamp: new Date(),
            });
            setIsProcessing(false);
          }
          if (data.status === 'error') {
            setError(data.text || 'Transcription error');
            setIsProcessing(false);
          }
          break;

        case 'audio':
          // Server sends assistant PCM16 audio as base64
          playAudio(data.data, data.format || 'audio/wav', []);
          setIsSpeaking(true);
          // Fallback timer to clear speaking state
          setTimeout(() => setIsSpeaking(false), 1500);
          break;

        case 'agent_switched':
          setTranscription('');
          setIsProcessing(false);
          setIsSpeaking(false);
          break;

        case 'error':
          // Check if it's a configuration error - show friendly message
          if (data.message?.includes('not configured') || data.message?.includes('AZURE_VOICELIVE')) {
            setError('Voice coming soon - Azure VoiceLive integration pending');
          } else {
            setError(data.message || 'Unknown error');
          }
          setIsProcessing(false);
          break;
      }
    },
    [playAudio]
  );

  // Initialize WebSocket connection
  useEffect(() => {
    const sessionId = `voicelive-${Date.now()}`;
    const baseWs = import.meta.env.VITE_WS_URL || 'ws://localhost:8082';
    const wsUrl = `${baseWs}/api/v1/voice/voicelive/${sessionId}`;

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setConnectionStatus('connected');
      // Set initial agent
      ws.send(JSON.stringify({ type: 'agent', agent_id: agentId }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data) as IncomingMessage;
      handleWebSocketMessage(data);
    };

    ws.onerror = (wsError) => {
      console.error('Voice WebSocket error:', wsError);
      setError('Connection error');
      setConnectionStatus('error');
    };

    ws.onclose = () => {
      setConnectionStatus('error');
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, [agentId, handleWebSocketMessage]);

  // Notify parent of connection status changes
  useEffect(() => {
    onStatusChangeRef.current?.(connectionStatus);
  }, [connectionStatus]);

  // Send agent switch when agentId changes and socket ready
  useEffect(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'agent', agent_id: agentId }));
    }
  }, [agentId]);

  // Start recording
  const startListening = async () => {
    try {
      setError(null);
      if (connectionStatus !== 'connected') {
        setError('Voice connection not ready');
        return;
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { channelCount: 1, sampleRate: 16000 },
      });
      streamRef.current = stream;

      // Audio context for level visualization and PCM16 capture
      audioContextRef.current = new AudioContext({ sampleRate: 16000 });
      const source = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
      source.connect(analyserRef.current);
      updateAudioLevel();

      const processor = audioContextRef.current.createScriptProcessor(4096, 1, 1);
      processor.onaudioprocess = (event) => {
        const input = event.inputBuffer.getChannelData(0);
        const pcm16 = new Int16Array(input.length);
        for (let i = 0; i < input.length; i++) {
          const s = Math.max(-1, Math.min(1, input[i]));
          pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
        }
        const bytes = new Uint8Array(pcm16.buffer);
        const base64 = btoa(String.fromCharCode(...bytes));
        wsRef.current?.send(JSON.stringify({ type: 'audio', data: base64 }));
      };

      source.connect(processor);
      processor.connect(audioContextRef.current.destination);
      processorRef.current = processor;

      setIsListening(true);
      setTranscription('');
      setIsProcessing(true);
    } catch (e) {
      console.error('Failed to start recording:', e);
      setError('Microphone access denied');
    }
  };

  // Stop recording
  const stopListening = () => {
    if (!isListening) return;

    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current.onaudioprocess = null;
      processorRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => { });
      audioContextRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    cancelAnimationFrame(animationFrameRef.current);
    setAudioLevel(0);
    setIsListening(false);
    wsRef.current?.send(JSON.stringify({ type: 'cancel' }));
  };

  // Update audio level visualization
  const updateAudioLevel = () => {
    if (analyserRef.current) {
      const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
      analyserRef.current.getByteFrequencyData(dataArray);

      // Calculate average level
      const average = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
      setAudioLevel(average / 255);

      animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
    }
  };

  // Get button state class
  const getButtonClass = () => {
    if (disabled) return 'voice-button disabled';
    if (connectionStatus === 'connecting') return 'voice-button disabled';
    if (connectionStatus === 'error') return 'voice-button disabled';
    if (isListening) return 'voice-button listening';
    if (isProcessing) return 'voice-button processing';
    if (isSpeaking) return 'voice-button speaking';
    return 'voice-button';
  };

  return (
    <div className="voice-chat">
      {/* Audio element for playback */}
      <audio ref={audioRef} style={{ display: 'none' }} />

      {/* Voice Button */}
      <div className="voice-button-container">
        <button
          className={getButtonClass()}
          onMouseDown={startListening}
          onMouseUp={stopListening}
          onMouseLeave={stopListening}
          onTouchStart={startListening}
          onTouchEnd={stopListening}
          disabled={disabled || isProcessing || isSpeaking}
          title={isListening ? 'Release to send' : 'Hold to speak'}
        >
          <div
            className="voice-ring"
            style={{
              transform: `scale(${1 + audioLevel * 0.5})`,
              opacity: isListening ? 0.8 : 0
            }}
          />

          <div className="voice-icon">
            {isListening && (
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
                <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
              </svg>
            )}
            {isProcessing && (
              <div className="processing-spinner" />
            )}
            {isSpeaking && (
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z" />
              </svg>
            )}
            {!isListening && !isProcessing && !isSpeaking && (
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
                <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
              </svg>
            )}
          </div>
        </button>

        <span className="voice-status">
          {connectionStatus === 'connecting' && 'Connecting to voice...'}
          {connectionStatus === 'error' && error?.includes('coming soon') && 'Voice integration pending'}
          {connectionStatus === 'error' && !error?.includes('coming soon') && 'Voice connection error'}
          {isListening && 'Listening...'}
          {isProcessing && 'Processing...'}
          {isSpeaking && `${agentId === 'marcus' ? 'Marcus' : 'Elena'} speaking...`}
          {!isListening && !isProcessing && !isSpeaking && connectionStatus === 'connected' && 'Hold to speak'}
        </span>
      </div>

      {/* Transcription Display */}
      {transcription && (
        <div className="transcription">
          <span className="transcription-label">You said:</span>
          <span className="transcription-text">{transcription}</span>
        </div>
      )}

      {/* Error/Info Display */}
      {error && (
        <div className={`voice-error ${error.includes('coming soon') ? 'voice-info' : ''}`}>
          {error}
        </div>
      )}
    </div>
  );
}

