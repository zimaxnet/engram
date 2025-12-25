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
    // Normalize trailing slash to avoid accidental double slashes
    this.baseUrl = baseUrl.replace(/\/$/, '')
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    // Health is served at root (`/health`) rather than under `/api/v1`
    const url =
      endpoint === '/health'
        ? `${this.baseUrl}${endpoint}`
        : `${this.baseUrl}${API_VERSION}${endpoint}`

    const headers: Record<string, string> = {}
    if (options.headers instanceof Headers) {
      options.headers.forEach((value, key) => {
        headers[key] = value
      })
    } else if (Array.isArray(options.headers)) {
      for (const [key, value] of options.headers) {
        headers[key] = value
      }
    } else if (options.headers) {
      Object.assign(headers, options.headers as Record<string, string>)
    }

    // Default to JSON requests unless we're sending FormData (e.g. file uploads)
    if (!(options.body instanceof FormData) && !('Content-Type' in headers)) {
      headers['Content-Type'] = 'application/json'
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
    try {
      if (typeof localStorage !== 'undefined' && typeof localStorage.getItem === 'function') {
        return localStorage.getItem('auth_token')
      }
    } catch (e) {
      // ignore in test environments without localStorage
    }
    return null
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

  async deleteSession(sessionId: string) {
    return this.request<{ success: boolean; message: string }>(`/chat/session/${sessionId}`, {
      method: 'DELETE',
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

  // Memory API
  async searchMemory(query: string, limit: number = 10) {
    return this.request<{
      results: Array<{
        id: string
        content: string
        node_type: string
        confidence: number
        created_at: string
        metadata: Record<string, unknown>
      }>
      total_count: number
      query_time_ms: number
    }>('/memory/search', {
      method: 'POST',
      body: JSON.stringify({ query, limit }),
    })
  }

  async listEpisodes(limit: number = 20, offset: number = 0) {
    return this.request<{
      episodes: Array<{
        id: string
        summary: string
        turn_count: number
        agent_id: string
        started_at: string
        ended_at: string | null
        topics: string[]
      }>
      total_count: number
    }>(`/memory/episodes?limit=${limit}&offset=${offset}`)
  }

  async getMemoryGraph(query: string = '') {
    const params = new URLSearchParams()
    if (query) params.set('query', query)

    return this.request<{
      nodes: Array<{
        id: string
        content: string
        node_type: string
        degree: number
        metadata: Record<string, unknown>
      }>
      edges: Array<{
        id: string
        source: string
        target: string
        label?: string | null
        weight: number
      }>
    }>(`/memory/graph${params.toString() ? `?${params.toString()}` : ''}`)
  }

  async getEpisode(episodeId: string) {
    return this.request<{
      id: string
      transcript: Array<{
        role: string
        content: string
        metadata?: Record<string, unknown>
      }>
    }>(`/memory/episodes/${episodeId}`)
  }

  async addFact(content: string, metadata: Record<string, unknown> = {}) {
    return this.request<{
      success: boolean
      node_id: string
      message: string
    }>('/memory/facts', {
      method: 'POST',
      body: JSON.stringify({ content, metadata }),
    })
  }

  // Workflows
  async listWorkflows(status?: string, limit: number = 20, offset: number = 0) {
    const params = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
    })
    if (status) params.set('status', status)

    return this.request<{
      workflows: Array<{
        workflow_id: string
        workflow_type: string
        status: string
        agent_id?: string
        started_at: string
        completed_at?: string | null
        task_summary: string
        step_count?: number | null
        current_step?: string | null
      }>
      total_count: number
    }>(`/workflows?${params.toString()}`)
  }

  async getWorkflow(workflowId: string) {
    return this.request<unknown>(`/workflows/${workflowId}`);
  }

  async getWorkflowDetail(workflowId: string) {
    return this.request<{
      workflow_id: string
      workflow_type: string
      status: string
      agent_id?: string
      session_id?: string
      started_at?: string
      completed_at?: string
      task_summary: string
      steps: Array<{
        name: string
        status: string
        duration_label?: string
        attempts?: number
        meta?: string
        note?: string
      }>
      context_snapshot?: Array<{ k: string; v: string }>
      trace_id?: string
    }>(`/workflows/${workflowId}`)
  }

  async signalWorkflow(workflowId: string, signalName: string, payload: unknown = {}) {
    return this.request<{ success: boolean; message: string }>(`/workflows/${workflowId}/signal`, {
      method: 'POST',
      body: JSON.stringify({ signal_name: signalName, payload }),
    })
  }

  // BAU
  async listBauFlows() {
    return this.request<Array<{
      id: string
      title: string
      persona: string
      description: string
      cta: string
    }>>('/bau/flows')
  }

  async listBauArtifacts(limit: number = 20, offset: number = 0) {
    return this.request<Array<{
      id: string
      name: string
      ingested_at: string
      chips: string[]
    }>>(`/bau/artifacts?limit=${limit}&offset=${offset}`)
  }

  async startBauFlow(flowId: string, initialMessage?: string) {
    return this.request<{
      workflow_id: string
      session_id: string
      message: string
    }>(`/bau/flows/${flowId}/start`, {
      method: 'POST',
      body: JSON.stringify({ flow_id: flowId, initial_message: initialMessage }),
    })
  }

  // Metrics
  async getEvidenceTelemetry(range: '15m' | '1h' | '24h' | '7d' = '15m') {
    return this.request<{
      range_label: string
      reliability: Array<{
        label: string
        value: string
        status: 'ok' | 'warn' | 'bad'
        note?: string
      }>
      ingestion: Array<{
        label: string
        value: string
        status: 'ok' | 'warn' | 'bad'
        note?: string
      }>
      memory_quality: Array<{
        label: string
        value: string
        status: 'ok' | 'warn' | 'bad'
        note?: string
      }>
      alerts: Array<{
        id: string
        severity: 'P0' | 'P1' | 'P2' | 'P3'
        title: string
        detail: string
        time_label: string
        status: 'open' | 'closed'
      }>
      narrative: {
        elena: string
        marcus: string
      }
      changes: Array<{ label: string; value: string }>
    }>(`/metrics/evidence?range=${range}`)
  }

  // Validation
  async listGoldenDatasets() {
    return this.request<Array<{
      id: string
      name: string
      filename: string
      hash: string
      size_label: string
      anchors: string[]
    }>>('/validation/datasets')
  }

  async getLatestGoldenRun() {
    return this.request<{
      summary: {
        run_id: string
        dataset_id: string
        status: 'PASS' | 'FAIL' | 'WARN' | 'RUNNING'
        checks_total: number
        checks_passed: number
        started_at: string
        ended_at?: string
        duration_ms?: number
        trace_id?: string
        workflow_id?: string
        session_id?: string
      }
      checks: Array<{
        id: string
        name: string
        status: 'pending' | 'running' | 'pass' | 'fail' | 'warn'
        duration_ms?: number
        evidence_summary?: string
      }>
      narrative: {
        elena: string
        marcus: string
      }
    } | null>('/validation/runs/latest')
  }

  async runGoldenThread(datasetId: string, mode: 'deterministic' | 'acceptance' = 'deterministic') {
    return this.request<{
      summary: {
        run_id: string
        dataset_id: string
        status: 'PASS' | 'FAIL' | 'WARN' | 'RUNNING'
        checks_total: number
        checks_passed: number
        started_at: string
        ended_at?: string
        duration_ms?: number
        trace_id?: string
        workflow_id?: string
        session_id?: string
      }
      checks: Array<{
        id: string
        name: string
        status: 'pending' | 'running' | 'pass' | 'fail' | 'warn'
        duration_ms?: number
        evidence_summary?: string
      }>
      narrative: {
        elena: string
        marcus: string
      }
    }>('/validation/run', {
      method: 'POST',
      body: JSON.stringify({ dataset_id: datasetId, mode }),
    })
  }

  async getGoldenRun(runId: string) {
    return this.request<{
      summary: {
        run_id: string
        dataset_id: string
        status: 'PASS' | 'FAIL' | 'WARN' | 'RUNNING'
        checks_total: number
        checks_passed: number
        started_at: string
        ended_at?: string
        duration_ms?: number
        trace_id?: string
        workflow_id?: string
        session_id?: string
      }
      checks: Array<{
        id: string
        name: string
        status: 'pending' | 'running' | 'pass' | 'fail' | 'warn'
        duration_ms?: number
        evidence_summary?: string
      }>
      narrative: {
        elena: string
        marcus: string
      }
    }>(`/validation/runs/${runId}`)
  }

  // Admin
  async getSystemSettings() {
    return this.request<{
      app_name: string
      maintenance_mode: boolean
      default_agent: string
      theme: string
      log_level: string
    }>('/admin/settings')
  }

  async updateSystemSettings(settings: unknown) {
    return this.request<{
      app_name: string
      maintenance_mode: boolean
      default_agent: string
      theme: string
      log_level: string
    }>('/admin/settings', {
      method: 'PUT',
      body: JSON.stringify(settings),
    })
  }

  async listUsers() {
    return this.request<Array<{
      user_id: string
      email: string
      role: string
      active: boolean
      last_login?: string | null
    }>>('/admin/users')
  }

  async getAuditLogs() {
    return this.request<Array<{
      id: string
      timestamp: string
      user_id: string
      action: string
      resource: string
      details?: string | null
    }>>('/admin/audit')
  }

  // Stories
  async listStories() {
    return this.request<Array<{
      story_id: string
      topic: string
      created_at: string
      story_path: string
    }>>('/story/')
  }

  async getStory(storyId: string) {
    return this.request<{
      story_id: string
      topic: string
      story_content: string
      story_path: string
      diagram_spec?: Record<string, unknown> | null
      diagram_path?: string | null
      created_at: string
    }>(`/story/${storyId}`)
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

export const clearSession = (sessionId: string) => apiClient.deleteSession(sessionId)

export const checkHealth = () => apiClient.healthCheck()

export const listAgents = () => apiClient.listAgents()

export const getAgent = (agentId: string) => apiClient.getAgent(agentId)


export const searchMemory = (query: string, limit?: number) => apiClient.searchMemory(query, limit)

export const listEpisodes = (limit?: number, offset?: number) => apiClient.listEpisodes(limit, offset)
export const getEpisode = (episodeId: string) => apiClient.getEpisode(episodeId)

export const addFact = (content: string, metadata?: Record<string, unknown>) => apiClient.addFact(content, metadata)
export const getMemoryGraph = (query?: string) => apiClient.getMemoryGraph(query)

export const listWorkflows = (status?: string, limit?: number, offset?: number) => apiClient.listWorkflows(status, limit, offset);
export const getWorkflow = (workflowId: string) => apiClient.getWorkflow(workflowId);
export const getWorkflowDetail = (workflowId: string) => apiClient.getWorkflowDetail(workflowId);
export const signalWorkflow = (workflowId: string, signalName: string, payload?: unknown) => apiClient.signalWorkflow(workflowId, signalName, payload);

// BAU
export const listBauFlows = () => apiClient.listBauFlows();
export const listBauArtifacts = (limit?: number, offset?: number) => apiClient.listBauArtifacts(limit, offset);
export const startBauFlow = (flowId: string, initialMessage?: string) => apiClient.startBauFlow(flowId, initialMessage);

// Metrics
export const getEvidenceTelemetry = (range?: '15m' | '1h' | '24h' | '7d') => apiClient.getEvidenceTelemetry(range);

// Validation
export const listGoldenDatasets = () => apiClient.listGoldenDatasets();
export const getLatestGoldenRun = () => apiClient.getLatestGoldenRun();
export const runGoldenThread = (datasetId: string, mode?: 'deterministic' | 'acceptance') => apiClient.runGoldenThread(datasetId, mode);
export const getGoldenRun = (runId: string) => apiClient.getGoldenRun(runId);

// Stories
export const listStories = () => apiClient.listStories();
export const getStory = (storyId: string) => apiClient.getStory(storyId);

export const getSystemSettings = () => apiClient.getSystemSettings();
export const updateSystemSettings = (settings: unknown) => apiClient.updateSystemSettings(settings);
export const listUsers = () => apiClient.listUsers();
export const getAuditLogs = () => apiClient.getAuditLogs();
