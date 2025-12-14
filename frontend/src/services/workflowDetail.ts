export type StepStatus = 'completed' | 'running' | 'failed' | 'waiting'

export interface WorkflowStep {
  name: string
  status: StepStatus
  durationLabel?: string
  attempts?: number
  meta?: string
  note?: string
}

export interface WorkflowDetailModel {
  workflowId: string
  workflowType: string
  status: string
  agentId?: string
  sessionId?: string
  traceId?: string
  steps: WorkflowStep[]
  contextSnapshot: Array<{ k: string; v: string }>
}

import { getWorkflowDetail as apiGetWorkflowDetail } from './api'

export async function getWorkflowDetail(workflowId: string): Promise<WorkflowDetailModel> {
  const detail = await apiGetWorkflowDetail(workflowId)
  
  // Map backend response to frontend format
  return {
    workflowId: detail.workflow_id,
    workflowType: detail.workflow_type,
    status: detail.status,
    agentId: detail.agent_id,
    sessionId: detail.session_id,
    traceId: detail.trace_id,
    steps: (detail.steps || []).map((s: any) => ({
      name: s.name || s.step_name || '',
      status: (s.status || 'waiting').toLowerCase() as WorkflowStep['status'],
      durationLabel: s.duration_label || s.duration_ms ? `${s.duration_ms}ms` : undefined,
      attempts: s.attempts,
      meta: s.meta || s.metadata,
      note: s.note,
    })),
    contextSnapshot: detail.context_snapshot || [
      { k: 'Workflow ID', v: detail.workflow_id },
      { k: 'Status', v: detail.status },
      { k: 'Type', v: detail.workflow_type },
    ],
  }
}

// Keep mock function for backward compatibility in tests
export async function getWorkflowDetailMock(workflowId: string): Promise<WorkflowDetailModel> {
  return getWorkflowDetail(workflowId)
}
