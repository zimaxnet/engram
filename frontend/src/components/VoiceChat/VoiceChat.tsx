/**
 * VoiceChat Component (WebSocket Proxy Architecture)
 * 
 * Connects to backend WebSocket proxy which handles Azure VoiceLive connection.
 * Backend automatically persists transcripts to Zep memory.
 * 
 * This approach works with unified endpoints (services.ai.azure.com) which
 * don't support REST token endpoints.
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import './VoiceChat.css';
import { getAccessToken } from '../../auth/authConfig';

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
  onAvatarVideo?: (url: string | undefined) => void;  // Callback for avatar video URL
  onAvatarStream?: (stream: MediaStream | null) => void; // Callback for WebRTC stream
  onSpeaking?: (speaking: boolean) => void;
  disabled?: boolean;
}

export default function VoiceChat({
  agentId,
  sessionId: sessionIdProp,
  onMessage,
  onVisemes,
  onStatusChange,
  onAvatarVideo,
  onAvatarStream,
  onSpeaking,
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
  const [avatarVideoUrl, setAvatarVideoUrl] = useState<string | undefined>(undefined);

  const wsRef = useRef<WebSocket | null>(null);
  const videoWsRef = useRef<WebSocket | null>(null); // Fallback: Direct WebSocket to Azure (deprecated)
  const peerConnectionRef = useRef<RTCPeerConnection | null>(null); // WebRTC for avatar video
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
  const onAvatarVideoRef = useRef(onAvatarVideo);
  const onAvatarStreamRef = useRef(onAvatarStream);

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
    onAvatarVideoRef.current = onAvatarVideo;
    onAvatarStreamRef.current = onAvatarStream;
  }, [onMessage, onVisemes, onStatusChange, onAvatarVideo, onAvatarStream]);

  // Notify parent when avatar video URL changes (legacy support)
  useEffect(() => {
    if (onAvatarVideoRef.current) {
      onAvatarVideoRef.current(avatarVideoUrl);
    }
  }, [avatarVideoUrl]);

  // Notify parent of speaking state changes
  useEffect(() => {
    onSpeaking?.(isSpeaking);
  }, [isSpeaking, onSpeaking]);

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

    if (playbackContextRef.current.state === 'suspended') {
      try {
        playbackContextRef.current.resume();
      } catch (e) {
        console.warn("Failed to resume playback context:", e);
      }
    }

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

  // Main Connection Logic - WebSocket Proxy
  useEffect(() => {
    let mounted = true;

    const connectToBackend = async () => {
      try {
        setConnectionStatus('connecting');
        setError(null);

        // Get JWT token for authentication
        let token: string | null = null;
        try {
          token = await getAccessToken();
        } catch (error) {
          console.warn('Failed to get access token for voice WebSocket:', error);
          // Continue without token - backend will handle authentication
        }

        // Connect to backend WebSocket proxy endpoint
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8082';
        let wsUrl = apiUrl.replace(/^http/, 'ws') + `/api/v1/voice/voicelive/${activeSessionId}`;

        // Append token as query parameter if available
        if (token) {
          wsUrl += `?token=${encodeURIComponent(token)}`;
        } else {
          console.warn('No access token available for voice WebSocket - connection may fail if AUTH_REQUIRED=true');
        }

        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          if (!mounted) return;
          setConnectionStatus('connected');
          onStatusChangeRef.current?.('connected');

          // Backend handles agent configuration automatically based on session
          // If we need to switch agent, send agent message
          if (agentId) {
            ws.send(JSON.stringify({
              type: 'agent',
              agent_id: agentId
            }));
          }
        };

        ws.onmessage = (event) => {
          if (!mounted) return;

          try {
            const data = JSON.parse(event.data);

            switch (data.type) {
              case 'audio':
                // Audio chunk from assistant
                if (data.data) {
                  enqueueAudio(data.data);
                  setIsSpeaking(true);
                }
                break;

              case 'transcription':
                // Transcript updates (user or assistant)
                if (data.speaker === 'user') {
                  if (data.status === 'complete') {
                    // Final user transcript
                    const finalText = data.text || '';
                    setUserTranscription(finalText);
                    userTranscriptRef.current = '';
                    if (finalText) {
                      onMessageRef.current?.({
                        id: `user-${Date.now()}`,
                        type: 'user',
                        text: finalText,
                        timestamp: new Date()
                      });
                    }
                  } else if (data.status === 'processing') {
                    // Partial user transcript
                    setUserTranscription(data.text || '');
                    userTranscriptRef.current = data.text || '';
                  } else if (data.status === 'listening') {
                    setIsProcessing(true);
                  }
                } else if (data.speaker === 'assistant') {
                  if (data.status === 'complete') {
                    // Final assistant transcript
                    const finalText = data.text || '';
                    setAssistantTranscription(finalText);
                    assistantTranscriptRef.current = '';
                    setIsProcessing(false);
                    if (finalText) {
                      onMessageRef.current?.({
                        id: `assistant-${Date.now()}`,
                        type: 'agent',
                        text: finalText,
                        agentId,
                        timestamp: new Date()
                      });
                    }
                  } else if (data.status === 'processing') {
                    // Partial assistant transcript
                    setAssistantTranscription(data.text || '');
                    assistantTranscriptRef.current = data.text || '';
                    setIsProcessing(false);
                  }
                }
                break;

              case 'avatar_video':
                // Avatar video chunk from VoiceLive (streaming - not currently used)
                // Future: could assemble chunks into video blob
                if (data.data) {
                  setIsSpeaking(true);
                }
                break;

              case 'avatar_video_url':
                // Avatar video URL (final video)
                if (data.url) {
                  setAvatarVideoUrl(data.url);
                  setIsSpeaking(true);
                  console.log('Avatar video URL received:', data.url);
                }
                break;

              case 'agent_switched':
                // Agent was switched (backend confirms)
                console.log('Agent switched to:', data.agent_id);
                // Clear avatar when switching agents
                setAvatarVideoUrl(undefined);
                if (onAvatarStreamRef.current) {
                  onAvatarStreamRef.current(null);
                }
                // Close existing video connection if any
                if (videoWsRef.current) {
                  videoWsRef.current.close();
                  videoWsRef.current = null;
                }
                break;

              case 'video_connection_ready':
                // Backend has prepared video connection - use WebRTC instead of direct WebSocket
                console.log('🎥 Video connection ready, establishing WebRTC connection...');
                // Don't use the old WebSocket approach - use WebRTC
                // The backend message is just a signal to start WebRTC negotiation
                establishWebRTCVideoConnection();
                break;

              case 'avatar_sdp_answer':
              case 'avatar_answer':
                // Backend returns SDP answer for WebRTC avatar (both naming conventions supported)
                console.log('📥 Received SDP answer for avatar');
                if (data.sdp) {
                  handleSdpAnswer(data.sdp);
                }
                break;

              case 'remote_ice_candidate':
                // Backend forwards remote ICE candidate
                console.log('🧊 Received remote ICE candidate');
                if (data.candidate) {
                  handleRemoteIceCandidate(data.candidate);
                }
                break;

              case 'avatar_status':
                // Avatar status update (e.g., negotiating, connected)
                console.log('Avatar Status:', data.status, data.message);
                if (data.status === 'negotiating') {
                  // status is negotiating
                } else if (data.status === 'ready') {
                  setAvatarVideoUrl('webrtc://ready');
                }
                break;

              case 'error':
                console.error('VoiceLive Error:', data);
                setError(data.message || 'Unknown error');
                setConnectionStatus('error');
                onStatusChangeRef.current?.('error');
                break;

              default:
                console.log('Unknown message type:', data.type, data);
            }
          } catch (e) {
            console.error('Failed to parse WebSocket message:', e, event.data);
          }
        };

        ws.onerror = (e) => {
          console.error('Voice WebSocket error', e);
          if (mounted) {
            setError('Voice connection error. Check console for details.');
            setConnectionStatus('error');
            onStatusChangeRef.current?.('error');
          }
        };

        ws.onclose = (event) => {
          console.log('Voice WebSocket closed', event.code, event.reason);
          if (mounted) {
            setConnectionStatus('error');
            if (event.code === 1008) {
              const reason = event.reason || 'Invalid or missing token';
              console.error(`Voice WebSocket authentication failed: ${reason}`);
              setError(`Authentication failed: ${reason}. Please refresh and try again.`);
            } else if (event.code !== 1000) {
              // 1000 is normal closure, others are errors
              const reason = event.reason || 'Unknown reason';
              console.error(`Voice WebSocket closed with error: ${reason} (code: ${event.code})`);
              setError(`Connection closed: ${reason}`);
            }
            onStatusChangeRef.current?.('error');
          }
        };

        wsRef.current = ws;

      } catch (err: any) {
        if (!mounted) return;
        console.error('Connection failed:', err);
        setError(err.message || 'Failed to connect');
        setConnectionStatus('error');
        onStatusChangeRef.current?.('error');
      }
    };

    connectToBackend();

    return () => {
      mounted = false;
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      if (videoWsRef.current) {
        videoWsRef.current.close();
        videoWsRef.current = null;
      }
    };
  }, [activeSessionId]);

  // NOTE: Old WebSocket-based establishVideoConnection removed
  // Using WebRTC-based establishWebRTCVideoConnection instead (see below)

  // NEW: Establish WebRTC video connection for avatar
  // This is the proper implementation using WebRTC instead of broken WebSocket
  const establishWebRTCVideoConnection = useCallback(async () => {
    console.log('🎥 Starting WebRTC avatar video connection...');

    try {
      // Close existing connections
      if (peerConnectionRef.current) {
        peerConnectionRef.current.close();
        peerConnectionRef.current = null;
      }

      // 1. Fetch ICE credentials from backend
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8082';
      console.log('📡 Fetching ICE credentials from backend...');

      const iceResponse = await fetch(`${apiUrl}/api/v1/voice/avatar/ice-credentials`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ agent_id: agentId }),
      });

      if (!iceResponse.ok) {
        const errorText = await iceResponse.text();
        console.error('❌ Failed to get ICE credentials:', iceResponse.status, errorText);
        return;
      }

      const iceConfig = await iceResponse.json();
      console.log('✅ ICE credentials received:', {
        urls: iceConfig.urls,
        username: iceConfig.username?.substring(0, 10) + '...',
        ttl: iceConfig.ttl,
      });

      // 2. Create WebRTC peer connection with ICE servers
      // CRITICAL: Force relay transport for Azure Avatar (required for NAT traversal)
      // See docs/architecture/azure-avatar-integration.md for details
      const peerConnection = new RTCPeerConnection({
        iceServers: [{
          urls: iceConfig.urls,
          username: iceConfig.username,
          credential: iceConfig.credential,
        }],
        // iceTransportPolicy: 'relay', // Relaxed: Allow all transport types (P2P + Relay) to improve connection success
      });
      peerConnectionRef.current = peerConnection;

      // 3. Set up track handlers for video/audio streams
      peerConnection.ontrack = (event) => {
        console.log('📹 WebRTC track received:', event.track.kind);

        if (event.track.kind === 'video') {
          const stream = event.streams[0];
          console.log('✅ Avatar video stream connected');
          setIsSpeaking(true);
          // setAvatarVideoUrl('webrtc://connected'); // Removed: connection handled via onAvatarStream

          // Pass stream to parent for rendering
          if (onAvatarStreamRef.current) {
            onAvatarStreamRef.current(stream);
          }
        }

        if (event.track.kind === 'audio') {
          const audioElement = document.createElement('audio');
          audioElement.id = 'avatar-audio-player';
          audioElement.srcObject = event.streams[0];
          audioElement.autoplay = true;
          console.log('✅ Avatar audio stream connected');
        }
      };

      // 4. ICE candidate handling
      peerConnection.onicecandidate = (event) => {
        if (event.candidate) {
          console.log('🧊 ICE candidate:', event.candidate.type);
          if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
              type: 'ice_candidate',
              candidate: event.candidate.toJSON(),
            }));
          }
        }
      };

      peerConnection.oniceconnectionstatechange = () => {
        console.log('🔗 ICE connection state:', peerConnection.iceConnectionState);
        if (peerConnection.iceConnectionState === 'connected') {
          console.log('✅ WebRTC avatar connected!');
        } else if (peerConnection.iceConnectionState === 'failed') {
          console.error('❌ WebRTC connection failed');
        }
      };

      // 5. Add transceivers to receive video/audio
      peerConnection.addTransceiver('video', { direction: 'recvonly' });
      peerConnection.addTransceiver('audio', { direction: 'recvonly' });

      // 6. Create offer
      const offer = await peerConnection.createOffer();
      await peerConnection.setLocalDescription(offer);
      console.log('📤 SDP offer created');

      // 7. Send offer to backend for avatar session negotiation
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'avatar_connect',
          sdp: offer.sdp,
          agent_id: agentId,
        }));
        console.log('📤 SDP offer sent to backend for avatar negotiation');
      } else {
        console.warn('⚠️ Main WebSocket not connected, cannot send SDP offer');
      }

    } catch (error) {
      console.error('❌ Failed to establish WebRTC video connection:', error);
    }
  }, [agentId]);

  // Handle SDP answer from backend (for WebRTC avatar)
  const handleSdpAnswer = useCallback(async (sdp: string) => {
    if (!peerConnectionRef.current) {
      console.warn('⚠️ No peer connection to apply SDP answer');
      return;
    }

    try {
      await peerConnectionRef.current.setRemoteDescription({
        type: 'answer',
        sdp: sdp,
      });
      console.log('✅ SDP answer applied to peer connection');
    } catch (error) {
      console.error('❌ Failed to apply SDP answer:', error);
    }
  }, []);

  // Handle remote ICE candidate from backend
  const handleRemoteIceCandidate = useCallback(async (candidate: RTCIceCandidateInit) => {
    if (!peerConnectionRef.current) {
      console.warn('⚠️ No peer connection to add ICE candidate');
      return;
    }

    try {
      await peerConnectionRef.current.addIceCandidate(new RTCIceCandidate(candidate));
      console.log('✅ Remote ICE candidate added');
    } catch (error) {
      console.error('❌ Failed to add ICE candidate:', error);
    }
  }, []);

  // Handle agent switching when agentId prop changes
  useEffect(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN && agentId) {
      wsRef.current.send(JSON.stringify({
        type: 'agent',
        agent_id: agentId
      }));
    }
  }, [agentId]);

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
          // Send audio chunk to backend WebSocket proxy
          // Backend forwards to Azure VoiceLive
          wsRef.current.send(JSON.stringify({
            type: 'audio',
            data: base64
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

    // Backend handles VAD (Voice Activity Detection) automatically
    // No need to send commit/response.create - backend detects speech end
    // Just stop sending audio chunks

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
      <audio ref={audioRef} className="hidden-audio" />

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
              '--scale': 1 + audioLevel * 0.5,
              '--opacity': isListening ? 0.8 : 0
            } as React.CSSProperties}
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

