/**
 * VoiceChat Component (Direct Azure Realtime Architecture)
 * 
 * connects directly to Azure OpenAI Realtime API using ephemeral tokens.
 * Reports completed turns to backend for Zep ingestion.
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import { getVoiceToken, persistTurn } from '../../services/api'; // We'll need to add these to api.ts
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

interface VoiceChatProps {
  agentId: string;
  sessionId?: string;
  onMessage?: (message: VoiceMessage) => void;
  onVisemes?: (visemes: Viseme[]) => void;
  onStatusChange?: (status: 'connecting' | 'connected' | 'error') => void;
  disabled?: boolean;
}

export default function VoiceChat({
  agentId,
  sessionId: sessionIdProp,
  onMessage,
  onVisemes,
  onStatusChange,
  disabled = false
}: VoiceChatProps) {
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [userTranscription, setUserTranscription] = useState('');
  const [assistantTranscription, setAssistantTranscription] = useState('');
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'error'>('connecting');
  const [error, setError] = useState<string | null>(null);
  const [audioLevel, setAudioLevel] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const playbackContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const animationFrameRef = useRef<number>(0);
  const streamRef = useRef<MediaStream | null>(null);

  // Buffers for current turn
  const assistantTranscriptRef = useRef('');
  const userTranscriptRef = useRef('');

  // Store callbacks
  const onMessageRef = useRef(onMessage);
  const onVisemesRef = useRef(onVisemes);
  const onStatusChangeRef = useRef(onStatusChange);

  // Generate local session ID if not provided
  const [localSessionId] = useState(() => `voice-${Date.now()}`);
  const activeSessionId = sessionIdProp || localSessionId;

  // Refs for audio playback queue
  const audioQueueRef = useRef<Float32Array[]>([]);
  const isPlayingRef = useRef(false);
  const nextStartTimeRef = useRef(0);

  useEffect(() => {
    onMessageRef.current = onMessage;
    onVisemesRef.current = onVisemes;
    onStatusChangeRef.current = onStatusChange;
  }, [onMessage, onVisemes, onStatusChange]);

  // Audio Playback Context
  useEffect(() => {
    if (!playbackContextRef.current) {
      playbackContextRef.current = new AudioContext({ sampleRate: 24000 });
    }
    return () => {
      playbackContextRef.current?.close();
    };
  }, []);

  // Audio Processing Function (Recursive)
  const processAudioQueue = useCallback(function processQueue() {
    if (!playbackContextRef.current || audioQueueRef.current.length === 0) {
      isPlayingRef.current = false;
      setIsSpeaking(false);
      return;
    }

    isPlayingRef.current = true;
    setIsSpeaking(true);
    const audioData = audioQueueRef.current.shift();
    if (!audioData) return;

    const buffer = playbackContextRef.current.createBuffer(1, audioData.length, 24000);
    buffer.getChannelData(0).set(audioData);

    const source = playbackContextRef.current.createBufferSource();
    source.buffer = buffer;
    source.connect(playbackContextRef.current.destination);

    const currentTime = playbackContextRef.current.currentTime;
    const startTime = Math.max(currentTime, nextStartTimeRef.current);

    source.start(startTime);
    nextStartTimeRef.current = startTime + buffer.duration;

    source.onended = () => {
      processQueue();
    };
  }, []);

  // Enqueue Audio
  const enqueueAudio = useCallback((base64Audio: string) => {
    try {
      const binaryString = atob(base64Audio);
      const len = binaryString.length;
      const bytes = new Uint8Array(len);
      for (let i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      const int16 = new Int16Array(bytes.buffer);
      const float32 = new Float32Array(int16.length);
      for (let i = 0; i < int16.length; i++) {
        float32[i] = int16[i] / 32768.0;
      }

      audioQueueRef.current.push(float32);

      if (!isPlayingRef.current) {
        if (playbackContextRef.current) {
          nextStartTimeRef.current = playbackContextRef.current.currentTime;
        }
        processAudioQueue();
      }
    } catch (e) {
      console.error('Audio decode error:', e);
    }
  }, [processAudioQueue]);

  // Main Connection Logic
  useEffect(() => {
    let mounted = true;

    const connectToAzure = async () => {
      try {
        setConnectionStatus('connecting');
        setError(null);

        // 1. Get Ephemeral Token from specific agent endpoint
        const tokenResponse = await getVoiceToken(agentId, activeSessionId);

        // 2. Construct Realtime API URL
        // Endpoint comes from backend, e.g., https://<resource>.openai.azure.com/
        // We need wss://<resource>.openai.azure.com/openai/realtime?api-key=...&deployment=gpt-4o-realtime-preview-2024-10-01&api-version=2024-10-01-preview
        const endpointUrl = new URL(tokenResponse.endpoint);
        const protocol = endpointUrl.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = endpointUrl.host;
        const wsUrl = `${protocol}//${host}/openai/realtime?api-key=${tokenResponse.token}&deployment=gpt-4o-realtime-preview-2024-10-01&api-version=2024-10-01-preview`;

        const ws = new WebSocket(wsUrl, 'realtime-openai-v1-beta'); // 'openai-insecure-api-key' or similar might be needed if not using protocol

        ws.onopen = () => {
          if (!mounted) return;
          setConnectionStatus('connected');

          // Send initial session configuration
          // Note: Use 'session.update' event
          ws.send(JSON.stringify({
            type: 'session.update',
            session: {
              voice: agentId === 'marcus' ? 'echo' : 'alloy', // Map to Azure voices (shim, real map should be better)
              instructions: `You are ${agentId}. Respond concisely.`, // Basic instructions, ideally fetched from config
              input_audio_format: 'pcm16',
              output_audio_format: 'pcm16',
              turn_detection: {
                type: 'server_vad',
                threshold: 0.6,
                prefix_padding_ms: 300,
                silence_duration_ms: 800
              }
            }
          }));
        };

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);

          switch (data.type) {
            case 'response.audio.delta':
              enqueueAudio(data.delta);
              break;

            case 'response.audio_transcript.delta':
              assistantTranscriptRef.current += data.delta;
              setAssistantTranscription(assistantTranscriptRef.current);
              setIsProcessing(false);
              break;

            case 'response.audio_transcript.done':
              // Verify / Finalize assistant text
              const finalAssistantText = data.transcript;
              if (finalAssistantText) {
                onMessageRef.current?.({
                  id: `assistant-${Date.now()}`,
                  type: 'agent',
                  text: finalAssistantText,
                  agentId,
                  timestamp: new Date()
                });
                // Report to backend
                persistTurn({
                  session_id: activeSessionId,
                  agent_id: agentId,
                  role: 'assistant',
                  content: finalAssistantText
                });
              }
              assistantTranscriptRef.current = '';
              break;

            case 'conversation.item.input_audio_transcription.delta':
              userTranscriptRef.current += data.delta;
              setUserTranscription(userTranscriptRef.current);
              break;

            case 'conversation.item.input_audio_transcription.completed':
              const finalUserText = data.transcript;
              if (finalUserText) {
                setUserTranscription(finalUserText);
                onMessageRef.current?.({
                  id: `user-${Date.now()}`,
                  type: 'user',
                  text: finalUserText,
                  timestamp: new Date()
                });
                // Report to backend
                persistTurn({
                  session_id: activeSessionId,
                  agent_id: agentId,
                  role: 'user',
                  content: finalUserText
                });
              }
              userTranscriptRef.current = '';
              break;

            case 'input_audio_buffer.speech_started':
              setIsProcessing(true); // Actually, listening? No, user speaking.
              // VAD detected speech
              break;

            case 'error':
              console.error('Azure Realtime Error:', data);
              setError(data.error?.message || 'Unknown Azure error');
              break;
          }
        };

        ws.onerror = (e) => {
          console.error('WebSocket error', e);
          setError('Connection error');
          setConnectionStatus('error');
        };

        ws.onclose = () => {
          if (mounted) setConnectionStatus('error');
        };

        wsRef.current = ws;

      } catch (err: any) {
        if (!mounted) return;
        console.error('Connection failed:', err);
        setError(err.message || 'Failed to connect');
        setConnectionStatus('error');
      }
    };

    connectToAzure();

    return () => {
      mounted = false;
      wsRef.current?.close();
    };
  }, [agentId, activeSessionId]);

  // Mic Logic
  const startListening = async () => {
    try {
      if (connectionStatus !== 'connected') return;

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { channelCount: 1, sampleRate: 24000 }
      });
      streamRef.current = stream;

      audioContextRef.current = new AudioContext({ sampleRate: 24000 });
      const source = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioContextRef.current.createAnalyser();
      source.connect(analyserRef.current);
      updateAudioLevel();

      const processor = audioContextRef.current.createScriptProcessor(4096, 1, 1);
      processor.onaudioprocess = (e) => {
        const input = e.inputBuffer.getChannelData(0);
        // Resample/Convert to PCM16
        const pcm16 = new Int16Array(input.length);
        for (let i = 0; i < input.length; i++) {
          const s = Math.max(-1, Math.min(1, input[i]));
          pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
        }

        // Convert to Base64
        // Note: Performance heavy for main thread, but standard for these demos
        const bytes = new Uint8Array(pcm16.buffer);
        let binary = '';
        for (let i = 0; i < bytes.byteLength; i++) {
          binary += String.fromCharCode(bytes[i]);
        }
        const base64 = btoa(binary);

        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({
            type: 'input_audio_buffer.append',
            audio: base64
          }));
        }
      };

      source.connect(processor);
      processor.connect(audioContextRef.current.destination);
      processorRef.current = processor;

      setIsListening(true);
    } catch (e) {
      console.error('Mic error:', e);
      setError('Mic access denied');
    }
  };

  const stopListening = () => {
    if (!isListening) return;

    // Commit buffer
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'input_audio_buffer.commit'
      }));
      wsRef.current.send(JSON.stringify({
        type: 'response.create' // Trigger response generation
      }));
    }

    processorRef.current?.disconnect();
    processorRef.current = null;
    audioContextRef.current?.close();
    audioContextRef.current = null;
    streamRef.current?.getTracks().forEach(t => t.stop());
    streamRef.current = null;

    cancelAnimationFrame(animationFrameRef.current);
    setAudioLevel(0);
    setIsListening(false);
  };

  const updateAudioLevel = () => {
    if (analyserRef.current) {
      const array = new Uint8Array(analyserRef.current.frequencyBinCount);
      analyserRef.current.getByteFrequencyData(array);
      const avg = array.reduce((a, b) => a + b) / array.length;
      setAudioLevel(avg / 255);
      animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
    }
  };

  // Button Class Helper
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
      <audio ref={audioRef} style={{ display: 'none' }} />

      {/* Voice Button */}
      <div className="voice-button-container">
        <button
          className={getButtonClass()}
          onMouseDown={(e) => {
            if (e.button !== 0) return;
            startListening();
          }}
          onMouseUp={stopListening}
          onMouseLeave={stopListening}
          onTouchStart={(e) => {
            e.preventDefault(); // Prevent scrolling/ghost clicks
            startListening();
          }}
          onTouchEnd={(e) => {
            e.preventDefault();
            stopListening();
          }}
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

      {/* Error/Info Display */}
      {error && (
        <div className={`voice-error ${error.includes('coming soon') ? 'voice-info' : ''}`}>
          {error}
        </div>
      )}
    </div>
  );
}

