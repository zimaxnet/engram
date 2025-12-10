import { useState, useRef, useEffect, useMemo, type FormEvent, type CSSProperties } from 'react'
import type { Agent } from '../../types'
import { sendChatMessage, type ApiError } from '../../services/api'
import './ChatPanel.css'

interface ChatPanelProps {
  agent: Agent
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

export function ChatPanel({ agent, onMetricsUpdate }: ChatPanelProps) {
  // Component remounts when agent changes (via key prop in App.tsx)
  // So we can initialize state directly
  const initialMessage = useMemo(() => createWelcomeMessage(agent), [agent])

  const [messages, setMessages] = useState<Message[]>([initialMessage])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Initialize sessionId once
  const [sessionId] = useState<string>(() =>
    `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  )
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

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
        tokensUsed: response.tokens_used
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

  const toggleRecording = () => {
    setIsRecording(!isRecording)
    // TODO: Implement Azure Speech SDK integration
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
                <img
                  src={agent.avatarUrl}
                  alt={agent.name}
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="40" fill="%233b82f6"/></svg>'
                  }}
                />
              </div>
            )}
            <div className="message-content">
              {message.role === 'assistant' && (
                <div className="message-header">
                  <span className="message-name">{message.agentName}</span>
                </div>
              )}
              <div className="message-text">{message.content}</div>
              <div className="message-time">
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
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
        <button
          type="button"
          className={`voice-button ${isRecording ? 'recording' : ''}`}
          onClick={toggleRecording}
          title={isRecording ? 'Stop recording' : 'Start voice input'}
        >
          🎤
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
    </div>
  )
}

