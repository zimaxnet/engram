/**
 * API Service Layer
 * 
 * Centralized API client for backend communication
 * Handles authentication, error handling, and request/response transformation
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8082'
const API_VERSION = '/api/v1'

export interface ApiError {
  message: string
  code?: string
  status?: number
}

export class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${API_VERSION}${endpoint}`

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers as Record<string, string>,
    }

    // Add auth token if available
    const token = this.getAuthToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({
          message: `HTTP ${response.status}: ${response.statusText}`,
        }))
        throw {
          message: errorData.message || errorData.detail || 'Request failed',
          code: errorData.code,
          status: response.status,
        } as ApiError
      }

      return await response.json()
    } catch (error) {
      if (error && typeof error === 'object' && 'message' in error) {
        throw error as ApiError
      }
      throw {
        message: error instanceof Error ? error.message : 'Network error',
        code: 'NETWORK_ERROR',
      } as ApiError
    }
  }

  private getAuthToken(): string | null {
    // In production, get from auth context or localStorage
    return localStorage.getItem('auth_token')
  }

  // Chat API
  async sendMessage(content: string, agentId?: string, sessionId?: string) {
    return this.request<{
      message_id: string
      content: string
      agent_id: string
      agent_name: string
      timestamp: string
      tokens_used?: number
      latency_ms?: number
      session_id: string
    }>('/chat', {
      method: 'POST',
      body: JSON.stringify({
        content,
        agent_id: agentId,
        session_id: sessionId,
      }),
    })
  }

  // Health check
  async healthCheck() {
    return this.request<{ status: string; timestamp: string; version: string }>('/health')
  }

  // Agents API
  async listAgents() {
    return this.request<Array<{
      id: string
      name: string
      title: string
      tools: string[]
    }>>('/agents')
  }

  async getAgent(agentId: string) {
    return this.request<{
      id: string
      name: string
      title: string
      tools: string[]
    }>(`/agents/${agentId}`)
  }
}

// Singleton instance
export const apiClient = new ApiClient()

// Convenience functions
export const sendChatMessage = (
  content: string,
  agentId?: string,
  sessionId?: string
) => apiClient.sendMessage(content, agentId, sessionId)

export const checkHealth = () => apiClient.healthCheck()

export const getAgents = () => apiClient.listAgents()

export const getAgent = (agentId: string) => apiClient.getAgent(agentId)

