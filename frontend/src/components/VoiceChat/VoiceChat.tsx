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

interface WebSocketMessage {
  type: 'transcription' | 'response' | 'avatar_speaking' | 'error';
  text?: string;
  is_final?: boolean;
  audio?: string;
  audio_format?: string;
  visemes?: Viseme[];
  agent_id?: string;
  duration_ms?: number;
  message?: string;
}

interface VoiceChatProps {
  agentId: string;
  onMessage?: (message: VoiceMessage) => void;
  onVisemes?: (visemes: Viseme[]) => void;
  disabled?: boolean;
}

export default function VoiceChat({ 
  agentId, 
  onMessage, 
  onVisemes,
  disabled = false 
}: VoiceChatProps) {
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcription, setTranscription] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [audioLevel, setAudioLevel] = useState(0);
  
  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const animationFrameRef = useRef<number>(0);
  
  // Store callbacks in refs to avoid stale closures
  const onMessageRef = useRef(onMessage);
  const onVisemesRef = useRef(onVisemes);
  
  useEffect(() => {
    onMessageRef.current = onMessage;
    onVisemesRef.current = onVisemes;
  }, [onMessage, onVisemes]);

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
  const handleWebSocketMessage = useCallback((data: WebSocketMessage) => {
    switch (data.type) {
      case 'transcription':
        setTranscription(data.text || '');
        if (data.is_final && data.text) {
          onMessageRef.current?.({
            id: `user-${Date.now()}`,
            type: 'user',
            text: data.text,
            timestamp: new Date()
          });
        }
        setIsProcessing(false);
        break;
        
      case 'response':
        onMessageRef.current?.({
          id: `agent-${Date.now()}`,
          type: 'agent',
          text: data.text || '',
          agentId: data.agent_id,
          timestamp: new Date()
        });
        
        // Play audio response
        if (data.audio && data.audio_format) {
          playAudio(data.audio, data.audio_format, data.visemes || []);
        }
        break;
        
      case 'avatar_speaking':
        setIsSpeaking(true);
        setTimeout(() => setIsSpeaking(false), data.duration_ms || 0);
        break;
        
      case 'error':
        setError(data.message || 'Unknown error');
        setIsProcessing(false);
        break;
    }
  }, [playAudio]);

  // Initialize WebSocket connection
  useEffect(() => {
    const sessionId = `voice-${Date.now()}`;
    const wsUrl = `${import.meta.env.VITE_WS_URL || 'ws://localhost:8082'}/api/v1/voice/ws/${sessionId}`;
    
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log('Voice WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data) as WebSocketMessage;
      handleWebSocketMessage(data);
    };
    
    ws.onerror = (wsError) => {
      console.error('Voice WebSocket error:', wsError);
      setError('Connection error');
    };
    
    ws.onclose = () => {
      console.log('Voice WebSocket disconnected');
    };
    
    wsRef.current = ws;
    
    return () => {
      ws.close();
    };
  }, [handleWebSocketMessage]);

  // Start recording
  const startListening = async () => {
    try {
      setError(null);
      
      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Set up audio context for level visualization
      audioContextRef.current = new AudioContext();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
      source.connect(analyserRef.current);
      
      // Start level visualization
      updateAudioLevel();
      
      // Set up media recorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      const chunks: Blob[] = [];
      
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunks.push(e.data);
        }
      };
      
      mediaRecorder.onstop = async () => {
        // Stop level visualization
        cancelAnimationFrame(animationFrameRef.current);
        setAudioLevel(0);
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
        
        // Send audio to server
        if (chunks.length > 0) {
          setIsProcessing(true);
          const blob = new Blob(chunks, { type: 'audio/webm' });
          const buffer = await blob.arrayBuffer();
          const base64 = btoa(
            new Uint8Array(buffer).reduce(
              (data, byte) => data + String.fromCharCode(byte),
              ''
            )
          );
          
          wsRef.current?.send(JSON.stringify({
            type: 'audio',
            data: base64
          }));
          
          wsRef.current?.send(JSON.stringify({
            type: 'stop_listening'
          }));
        }
      };
      
      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start(100); // Collect in 100ms chunks
      
      wsRef.current?.send(JSON.stringify({
        type: 'start_listening'
      }));
      
      setIsListening(true);
      setTranscription('');
      
    } catch (e) {
      console.error('Failed to start recording:', e);
      setError('Microphone access denied');
    }
  };

  // Stop recording
  const stopListening = () => {
    if (mediaRecorderRef.current && isListening) {
      mediaRecorderRef.current.stop();
      setIsListening(false);
    }
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
                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
              </svg>
            )}
            {isProcessing && (
              <div className="processing-spinner" />
            )}
            {isSpeaking && (
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
              </svg>
            )}
            {!isListening && !isProcessing && !isSpeaking && (
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
              </svg>
            )}
          </div>
        </button>
        
        <span className="voice-status">
          {isListening && 'Listening...'}
          {isProcessing && 'Processing...'}
          {isSpeaking && `${agentId === 'marcus' ? 'Marcus' : 'Elena'} speaking...`}
          {!isListening && !isProcessing && !isSpeaking && 'Hold to speak'}
        </span>
      </div>
      
      {/* Transcription Display */}
      {transcription && (
        <div className="transcription">
          <span className="transcription-label">You said:</span>
          <span className="transcription-text">{transcription}</span>
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

