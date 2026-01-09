import { useState, useRef, useEffect, useMemo, type FormEvent, type CSSProperties } from 'react'
import type { Agent } from '../../types'
import { sendChatMessage, clearSession, type ApiError } from '../../services/api'
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './ChatPanel.css'

interface ChatPanelProps {
  agent: Agent
  sessionId?: string
  onMetricsUpdate: (metrics: SessionMetrics) => void
}

interface SessionMetrics {
  tokensUsed: number
  latency: number
  memoryNodes: number
  duration: number
  turns: number
  cost: number
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  agentId?: string
  agentName?: string
  timestamp: Date
  tokensUsed?: number
  avatarVideoUrl?: string  // Foundry avatar video URL (if available)
}

// Create initial welcome message
function createWelcomeMessage(agent: Agent): Message {
  return {
    id: Date.now().toString(),
    role: 'assistant',
    content: `Hello! I'm ${agent.name}, your ${agent.title}. How can I help you today?`,
    agentId: agent.id,
    agentName: agent.name,
    timestamp: new Date()
  }
}

// Voice Chat Overlay Styles
import VoiceChat from '../VoiceChat/VoiceChat';
import AvatarDisplay from '../AvatarDisplay/AvatarDisplay';

const overlayStyles: CSSProperties = {
  position: 'fixed',
  top: 0,
  left: 0,
  width: '100vw',
  height: '100vh',
  background: 'rgba(0, 0, 0, 0.85)',
  backdropFilter: 'blur(8px)',
  WebkitBackdropFilter: 'blur(8px)',
  zIndex: 2000,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  flexDirection: 'column',
  padding: '1rem',
};

const closeButtonStyles: CSSProperties = {
  position: 'absolute',
  top: '1rem',
  right: '1rem',
  background: 'rgba(255, 255, 255, 0.1)',
  border: 'none',
  borderRadius: '50%',
  width: '48px',
  height: '48px',
  color: 'white',
  fontSize: '1.5rem',
  cursor: 'pointer',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 2001,
};



export function ChatPanel({ agent, sessionId: sessionIdProp, onMetricsUpdate }: ChatPanelProps) {
  // Component remounts when agent changes (via key prop in App.tsx)
  // So we can initialize state directly
  const initialMessage = useMemo(() => createWelcomeMessage(agent), [agent])

  const [messages, setMessages] = useState<Message[]>([initialMessage])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Voice Live Mode State
  const [isVoiceOpen, setIsVoiceOpen] = useState(false)
  const [avatarStream, setAvatarStream] = useState<MediaStream | null>(null)
  const [isAvatarSpeaking, setIsAvatarSpeaking] = useState(false)

  // Auto-open voice mode on mount (Mobile-first experience)
  useEffect(() => {
    if (agent.voiceEnabled) {
      setIsVoiceOpen(true);
    }
  }, [agent.id, agent.voiceEnabled]);

  // Initialize local sessionId once (used when caller doesn't supply a shared sessionId)
  const [localSessionId] = useState<string>(() =>
    `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  )
  const sessionId = sessionIdProp || localSessionId
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Track if we've loaded history for this sessionId to avoid reloading
  const [loadedSessionId, setLoadedSessionId] = useState<string | null>(null)

  // Reset loadedSessionId and messages when sessionId changes
  useEffect(() => {
    if (sessionIdProp && sessionIdProp !== loadedSessionId) {
      // If we had a different session loaded, reset
      if (loadedSessionId && sessionIdProp !== loadedSessionId) {
        setLoadedSessionId(null)
        // Reset to welcome message when switching sessions
        setMessages([initialMessage])
      }
    }
  }, [sessionIdProp, loadedSessionId, initialMessage])

  // Load existing messages when sessionId is provided (e.g., from Episodes page)
  useEffect(() => {
    const loadSessionHistory = async () => {
      // Only load if:
      // 1. We have a sessionId prop (not a local one)
      // 2. We haven't loaded history for this sessionId yet
      // 3. We only have the welcome message
      if (sessionIdProp &&
        sessionIdProp !== loadedSessionId &&
        messages.length === 1 &&
        messages[0].role === 'assistant' &&
        messages[0].id === initialMessage.id) {
        try {
          const { getEpisode } = await import('../../services/api')
          const episodeData = await getEpisode(sessionIdProp)

          if (episodeData?.transcript && episodeData.transcript.length > 0) {
            // Convert transcript to Message format
            const loadedMessages: Message[] = episodeData.transcript.map((msg: { role: string; content: string }, index: number) => ({
              id: `loaded-${sessionIdProp}-${index}`,
              role: msg.role === 'user' ? 'user' : 'assistant',
              content: msg.content,
              agentId: msg.role === 'assistant' ? agent.id : undefined,
              agentName: msg.role === 'assistant' ? agent.name : undefined,
              timestamp: new Date(), // Transcript doesn't include timestamps, use current time
            }))

            // Replace welcome message with loaded history
            setMessages(loadedMessages)
            setLoadedSessionId(sessionIdProp)
          } else {
            // No history found, mark as loaded to avoid retrying
            setLoadedSessionId(sessionIdProp)
          }
        } catch (err) {
          console.warn('Failed to load session history:', err)
          // Mark as attempted to avoid retrying on every render
          setLoadedSessionId(sessionIdProp)
        }
      }
    }

    loadSessionHistory()
  }, [sessionIdProp, agent.id, agent.name, loadedSessionId, messages, initialMessage.id])

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isTyping) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    }

    const userInput = input.trim()
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsTyping(true)
    setError(null)

    try {
      // Call backend API
      const response = await sendChatMessage(userInput, agent.id, sessionId)

      const assistantMessage: Message = {
        id: response.message_id,
        role: 'assistant',
        content: response.content,
        agentId: response.agent_id,
        agentName: response.agent_name,
        timestamp: new Date(response.timestamp),
        tokensUsed: response.tokens_used,
        avatarVideoUrl: response.avatar_video_url,  // Include avatar video URL if available
      }

      setMessages(prev => [...prev, assistantMessage])
      setIsTyping(false)

      // Update metrics
      const totalMessages = messages.length + 2
      onMetricsUpdate({
        tokensUsed: response.tokens_used || 0,
        latency: (response.latency_ms || 0) / 1000,
        memoryNodes: Math.floor(Math.random() * 20) + 30, // TODO: Get from API
        duration: Math.floor((Date.now() - new Date(messages[0]?.timestamp || Date.now()).getTime()) / 60000),
        turns: totalMessages,
        cost: (response.tokens_used || 0) * 0.00003 // Approximate cost per token
      })
    } catch (err) {
      setIsTyping(false)
      const apiError = err as ApiError
      setError(apiError.message || 'Failed to send message. Please try again.')

      // Show error message in chat
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `I apologize, but I encountered an error: ${apiError.message}. Please try again.`,
        agentId: agent.id,
        agentName: agent.name,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    }
  }

  const handleClearSession = async () => {
    if (!window.confirm('Clear session? This will reset conversation context.')) return

    // Resolve sessionId from prop or local state
    const sid = sessionIdProp || localSessionId;

    try {
      await clearSession(sid)
      setMessages([createWelcomeMessage(agent)])
      setInput('')
      setError(null)
    } catch (err: any) {
      setError(`Failed to clear session: ${err.message}`)
    }
  }

  const toggleVoiceMode = () => {
    setIsVoiceOpen(!isVoiceOpen)
  }



  return (
    <div className="chat-panel">
      {/* Messages Area */}
      <div className="chat-messages">
        {messages.map(message => (
          <div
            key={message.id}
            className={`message ${message.role}`}
            style={message.role === 'assistant' ? { '--agent-color': agent.accentColor } as CSSProperties : undefined}
          >
            {message.role === 'assistant' && (
              <div className="message-avatar">
                {message.avatarVideoUrl ? (
                  // Show Foundry avatar video if available
                  <video
                    src={message.avatarVideoUrl}
                    autoPlay
                    loop={false}
                    muted={false}
                    playsInline
                    className="avatar-video"
                    style={{
                      width: '100%',
                      height: '100%',
                      objectFit: 'cover',
                      borderRadius: '50%',
                    }}
                    onError={(e) => {
                      // Fallback to static image if video fails
                      const target = e.target as HTMLVideoElement;
                      const img = document.createElement('img');
                      img.src = agent.avatarUrl;
                      img.alt = agent.name;
                      img.onerror = () => {
                        img.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="40" fill="%233b82f6"/></svg>';
                      };
                      target.parentElement?.replaceChild(img, target);
                    }}
                  />
                ) : (
                  // Fallback to static image
                  <img
                    src={agent.avatarUrl}
                    alt={agent.name}
                    onError={(e: React.SyntheticEvent<HTMLImageElement, Event>) => {
                      (e.target as HTMLImageElement).src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="40" fill="%233b82f6"/></svg>'
                    }}
                  />
                )}
              </div>
            )}
            <div className="message-content">
              {message.role === 'assistant' && (
                <div className="message-header">
                  <span className="message-name">{message.agentName}</span>
                </div>
              )}
              {/* Render Markdown for better UX */}
              <div className="message-text markdown-body">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    img: (props) => (
                      <img
                        {...props}
                        style={{ maxWidth: '100%', borderRadius: '8px', marginTop: '10px' }}
                        loading="lazy"
                      />
                    )
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
              <div className="message-footer">
                <span className="message-time">
                  {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
                {message.role === 'assistant' && message.tokensUsed !== undefined && (
                  <span className="message-metrics">
                    · {message.tokensUsed} tokens
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="message assistant" style={{ '--agent-color': agent.accentColor } as CSSProperties}>
            <div className="message-avatar">
              <img src={agent.avatarUrl} alt={agent.name} />
            </div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Error Display */}
      {error && (
        <div className="chat-error">
          <span className="error-icon">⚠️</span>
          <span className="error-message">{error}</span>
          <button
            className="error-dismiss"
            onClick={() => setError(null)}
            aria-label="Dismiss error"
          >
            ×
          </button>
        </div>
      )}

      {/* Input Area */}
      <form className="chat-input-area" onSubmit={handleSubmit}>
        {agent.voiceEnabled && (
          <button
            type="button"
            className={`voice-button ${isVoiceOpen ? 'recording' : ''}`}
            onClick={toggleVoiceMode}
            title={'Tap to talk (Voice Live)'}
          >
            🎤
          </button>
        )}
        <button
          type="button"
          onClick={handleClearSession}
          className="voice-button"
          title="Clear Session"
          disabled={isTyping}
        >
          🧹
        </button>
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={`Ask ${agent.name.split(' ')[0]} anything...`}
          className="chat-input"
          disabled={isTyping}
        />
        <button
          type="submit"
          className="send-button"
          disabled={!input.trim() || isTyping}
        >
          Send →
        </button>
      </form>

      {/* Voice Overlay */}
      {
        isVoiceOpen && (
          <div style={overlayStyles}>
            <button
              style={closeButtonStyles}
              onClick={() => setIsVoiceOpen(false)}
              aria-label="Close voice chat"
            >
              ×
            </button>
            <div style={{
              background: 'var(--glass-bg)',
              border: '1px solid var(--glass-border)',
              borderRadius: '16px',
              padding: '2rem',
              width: '100%',
              maxWidth: '500px',
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '1.5rem',
              backdropFilter: 'blur(16px)',
              WebkitBackdropFilter: 'blur(16px)',
            }}>
              <h3 style={{ margin: 0, fontWeight: 600 }}>Speaking with {agent.name}</h3>

              {/* Avatar Display (WebRTC Video) */}
              <div style={{ width: '200px', height: '200px', margin: '0 0' }}>
                <AvatarDisplay
                  agentId={agent.id as 'elena' | 'marcus' | 'sage'}
                  isSpeaking={isAvatarSpeaking}
                  avatarStream={avatarStream}
                  size="lg"
                  showName={false}
                />
              </div>

              <VoiceChat
                agentId={agent.id}
                sessionId={sessionId}
                onStatusChange={(status) => {
                  if (status === 'error') {
                    // Optional: handle error state
                  }
                }}
                onAvatarStream={setAvatarStream}
                onSpeaking={setIsAvatarSpeaking}
              />
              <p style={{
                fontSize: '0.875rem',
                color: 'var(--color-text-dim)',
                textAlign: 'center',
                margin: 0
              }}>
                Press and hold the ring to speak.
                Stories and visuals created here will appear in the chat.
              </p>
            </div>
          </div>
        )
      }
    </div >
  )
}

