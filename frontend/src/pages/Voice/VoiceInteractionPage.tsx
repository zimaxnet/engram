import { useState, useRef, useEffect, useCallback } from 'react';
import './VoiceInteractionPage.css';
import VoiceChat from '../../components/VoiceChat/VoiceChat';
import AvatarDisplay from '../../components/AvatarDisplay/AvatarDisplay';
import type { AgentId } from '../../types';

interface VoiceInteractionPageProps {
  activeAgent: AgentId;
  sessionId: string;
}

/**
 * Mobile-First Voice Interaction Page
 * 
 * Elena's avatar is front-and-center with WebRTC video streaming.
 * Push-to-talk interface optimized for touch devices.
 */
export function VoiceInteractionPage({ activeAgent, sessionId }: VoiceInteractionPageProps) {
  const [status, setStatus] = useState<'connecting' | 'connected' | 'error'>('connecting');
  const [isSpeaking] = useState(false); // TODO: Wire up when VoiceChat exposes speaking state
  const [avatarStream, setAvatarStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Video element ref for WebRTC stream
  const videoRef = useRef<HTMLVideoElement>(null);

  // Attach WebRTC stream to video element
  useEffect(() => {
    if (videoRef.current && avatarStream) {
      videoRef.current.srcObject = avatarStream;
      videoRef.current.play().catch(e => console.warn('Video autoplay blocked:', e));
    }
  }, [avatarStream]);

  // Handle avatar stream from VoiceChat
  const handleAvatarStream = useCallback((stream: MediaStream | null) => {
    setAvatarStream(stream);
    if (stream) {
      console.log('📹 Avatar video stream received');
    }
  }, []);

  // Handle status changes
  const handleStatusChange = useCallback((newStatus: 'connecting' | 'connected' | 'error') => {
    setStatus(newStatus);
    if (newStatus === 'error') {
      setError('Voice connection failed. Check your network and try again.');
    } else {
      setError(null);
    }
  }, []);

  const agentName = activeAgent === 'elena' ? 'Dr. Elena Vasquez'
    : activeAgent === 'marcus' ? 'Marcus Chen'
      : 'Sage Meridian';

  const agentRole = activeAgent === 'elena' ? 'Business Analyst'
    : activeAgent === 'marcus' ? 'Project Manager'
      : 'Storyteller';

  return (
    <div className="voice-page">
      {/* Avatar Section - Mobile: Top, Desktop: Left */}
      <section className="avatar-section">
        <div className={`avatar-container ${isSpeaking ? 'speaking' : ''}`}>
          {avatarStream ? (
            // WebRTC Video Stream
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted={false}
              className="avatar-video-stream"
            />
          ) : (
            // Fallback to static avatar
            <AvatarDisplay
              agentId={activeAgent}
              isSpeaking={isSpeaking}
              expression={status === 'connected' ? 'neutral' : 'thinking'}
              showName={false}
              size="lg"
              avatarStream={avatarStream}
            />
          )}
        </div>

        <div className="agent-info">
          <h2>{agentName}</h2>
          <p className="role">{agentRole}</p>

          <div className="connection-status">
            <span className={`status-dot ${isSpeaking ? 'speaking' :
              status === 'connected' ? 'connected' :
                status === 'connecting' ? 'connecting' : 'error'
              }`} />
            <span>
              {isSpeaking ? 'Speaking...' :
                status === 'connected' ? 'Ready' :
                  status === 'connecting' ? 'Connecting...' : 'Disconnected'}
            </span>
          </div>
        </div>
      </section>

      {/* Controls Section - Mobile: Bottom, Desktop: Right */}
      <section className="controls-section">
        {error && (
          <div className="error-banner">
            <p>{error}</p>
            <button onClick={() => {
              setError(null);
              setStatus('connecting');
            }}>
              Retry Connection
            </button>
          </div>
        )}

        {/* VoiceChat handles the push-to-talk and audio processing */}
        <VoiceChat
          agentId={activeAgent}
          sessionId={sessionId}
          disabled={status !== 'connected'}
          onStatusChange={handleStatusChange}
          onAvatarStream={handleAvatarStream}
        />
      </section>
    </div>
  );
}
