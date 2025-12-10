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

  // Memory API
  async searchMemory(query: string, limit: number = 10) {
    return this.request<{
      results: Array<{
        id: string
        content: string
        node_type: string
        confidence: number
        created_at: string
        metadata: Record<string, any>
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

  async getEpisode(episodeId: string) {
    return this.request<{
      id: string
      transcript: Array<{
        role: string
        content: string
        metadata?: Record<string, any>
      }>
    }>(`/memory/episodes/${episodeId}`)
  }

  async addFact(content: string, metadata: Record<string, any> = {}) {
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
    // Engram Project Workflows (Source of Truth)
    const workflows = [
      // GitHub Actions (CI/CD)
      {
        workflow_id: 'gh-ci-pipeline',
        workflow_type: 'GitHubAction',
        status: 'completed',
        agent_id: 'system',
        started_at: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
        task_summary: 'CI Pipeline: Linting, Unit Tests, and Docker Build (ci.yml)',
        step_count: 4,
        current_step: 'Complete',
      },
      {
        workflow_id: 'gh-deploy-azure',
        workflow_type: 'GitHubAction',
        status: 'running',
        agent_id: 'system',
        started_at: new Date(Date.now() - 1000 * 60 * 10).toISOString(),
        task_summary: 'Deploy to Azure: Bicep Provisioning & Container App Revision (deploy.yml)',
        step_count: 6,
        current_step: 'Deploying Worker Container',
      },
      {
        workflow_id: 'gh-wiki-sync',
        workflow_type: 'GitHubAction',
        status: 'waiting',
        agent_id: 'system',
        started_at: new Date(Date.now() - 1000 * 60 * 300).toISOString(),
        task_summary: 'Documentation Sync: Publishing wiki updates to gh-pages (wiki.yml)',
        step_count: 2,
        current_step: 'Waiting for merge',
      },

      // Temporal Workflows (Agentic)
      {
        workflow_id: 'temporal-agent-execution-001',
        workflow_type: 'AgentWorkflow',
        status: 'running',
        agent_id: 'marcus',
        started_at: new Date(Date.now() - 1000 * 60 * 2).toISOString(),
        task_summary: 'Orchestrating multi-step reasoning task (agent_workflow.py)',
        step_count: 10,
        current_step: 'Executing Activity: search_memory',
      },
      {
        workflow_id: 'temporal-long-running-etl',
        workflow_type: 'EtlWorkflow',
        status: 'completed',
        agent_id: 'data-bot',
        started_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
        task_summary: 'Processing Unstructured.io document ingestion pipeline',
        step_count: 5,
        current_step: 'Complete',
      }
    ];

    let filtered = workflows;
    if (status) {
      filtered = workflows.filter(w => w.status === status);
    }

    return Promise.resolve({ workflows: filtered, total_count: filtered.length });
  }

  async getWorkflow(workflowId: string) {
    return this.request<any>(`/workflows/${workflowId}`);
  }

  async signalWorkflow(workflowId: string, signalName: string, payload: any = {}) {
    // Mock signal
    console.log(`Signaling ${workflowId} with ${signalName}`, payload);
    return Promise.resolve({ success: true });
  }

  // Admin
  async getSystemSettings() {
    return Promise.resolve({
      model_name: "gemini-1.5-pro",
      temperature: 0.7,
      max_tokens: 4096,
      memory_backend: "zep (cloud)",
      workflow_backend: "temporal (local)",
      theme: "engram-dark",
      log_level: "VERBOSE"
    });
  }

  async updateSystemSettings(settings: any) {
    console.log("Updating settings", settings);
    return Promise.resolve({ success: true });
  }

  async listUsers() {
    return Promise.resolve([
      {
        user_id: 'u-derek',
        email: 'derek@zimax.net',
        role: 'SUPER_ADMIN',
        active: true,
        last_login: new Date().toISOString()
      },
      {
        user_id: 'u-antigravity',
        email: 'system@engram.work',
        role: 'SYSTEM_AGENT',
        active: true,
        last_login: new Date(Date.now() - 10000).toISOString()
      },
      {
        user_id: 'u-monitor',
        email: 'monitor@engram.work',
        role: 'VIEWER',
        active: true,
        last_login: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString()
      }
    ]);
  }

  async getAuditLogs() {
    return Promise.resolve([
      { id: 'l-1025', action: 'DEPLOY_SUCCESS', resource: 'infra/worker-aca', user_id: 'gh-actions', timestamp: new Date().toISOString() },
      { id: 'l-1024', action: 'INFRA_UPDATE', resource: 'infra/main.bicep', user_id: 'u-derek', timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString() },
      { id: 'l-1023', action: 'API_KEY_ROTATION', resource: 'settings/keys', user_id: 'u-antigravity', timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString() },
      { id: 'l-1022', action: 'USER_LOGIN', resource: 'auth', user_id: 'u-derek', timestamp: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString() },
      { id: 'l-1021', action: 'SYSTEM_INIT', resource: 'core', user_id: 'system', timestamp: '2025-11-20T09:00:00Z' }
    ]);
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

export const listAgents = () => apiClient.listAgents()

export const getAgent = (agentId: string) => apiClient.getAgent(agentId)


export const searchMemory = (query: string, limit?: number) => apiClient.searchMemory(query, limit)

export const listEpisodes = (limit?: number, offset?: number) => apiClient.listEpisodes(limit, offset)
export const getEpisode = (episodeId: string) => apiClient.getEpisode(episodeId)

export const addFact = (content: string, metadata?: Record<string, any>) => apiClient.addFact(content, metadata)

export const listWorkflows = (status?: string, limit?: number, offset?: number) => apiClient.listWorkflows(status, limit, offset);
export const getWorkflow = (workflowId: string) => apiClient.getWorkflow(workflowId);
export const signalWorkflow = (workflowId: string, signalName: string, payload?: any) => apiClient.signalWorkflow(workflowId, signalName, payload);

export const getSystemSettings = () => apiClient.getSystemSettings();
export const updateSystemSettings = (settings: any) => apiClient.updateSystemSettings(settings);
export const listUsers = () => apiClient.listUsers();
export const getAuditLogs = () => apiClient.getAuditLogs();
