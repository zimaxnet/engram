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
      filtered = workflows.filter(w => w.status === status)
    }

    const paginated = filtered.slice(offset, offset + limit);

    return {
      workflows: paginated,
      total_count: filtered.length
    };
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

  async updateSystemSettings(settings: unknown) {
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

export const addFact = (content: string, metadata?: Record<string, unknown>) => apiClient.addFact(content, metadata)

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

export const getSystemSettings = () => apiClient.getSystemSettings();
export const updateSystemSettings = (settings: unknown) => apiClient.updateSystemSettings(settings);
export const listUsers = () => apiClient.listUsers();
export const getAuditLogs = () => apiClient.getAuditLogs();
