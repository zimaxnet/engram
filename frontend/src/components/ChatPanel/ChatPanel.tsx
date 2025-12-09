import { useState, useRef, useEffect, useMemo } from 'react'
import type { Agent } from '../../App'
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
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsTyping(true)

    // Simulate API call
    setTimeout(() => {
      const responseContent = agent.id === 'elena'
        ? `I understand your question about "${input.substring(0, 30)}...". Let me analyze this from a requirements perspective. Could you tell me more about the stakeholders involved and the business outcomes you're hoping to achieve?`
        : `Thanks for bringing this up. From a project management standpoint, I'd want to understand: What's your timeline? What resources do you have available? And what does success look like for this initiative?`

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: responseContent,
        agentId: agent.id,
        agentName: agent.name,
        timestamp: new Date(),
        tokensUsed: Math.floor(Math.random() * 200) + 100
      }

      setMessages(prev => [...prev, assistantMessage])
      setIsTyping(false)

      // Update metrics
      onMetricsUpdate({
        tokensUsed: messages.length * 150 + (assistantMessage.tokensUsed || 0),
        latency: Math.random() * 0.5 + 0.3,
        memoryNodes: Math.floor(Math.random() * 20) + 30,
        duration: Math.floor((Date.now() - new Date(messages[0]?.timestamp || Date.now()).getTime()) / 60000),
        turns: messages.length + 2,
        cost: (messages.length * 150 + (assistantMessage.tokensUsed || 0)) * 0.00003
      })
    }, 1000 + Math.random() * 1000)
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
            style={message.role === 'assistant' ? { '--agent-color': agent.accentColor } as React.CSSProperties : undefined}
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
          <div className="message assistant" style={{ '--agent-color': agent.accentColor } as React.CSSProperties}>
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

