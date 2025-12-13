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

export async function getWorkflowDetailMock(workflowId: string): Promise<WorkflowDetailModel> {
  const isAgent = workflowId.includes('AgentWorkflow') || workflowId.startsWith('temporal-agent')

  const steps: WorkflowStep[] = isAgent
    ? [
        { name: 'initialize_context', status: 'completed', durationLabel: '120ms', attempts: 1 },
        { name: 'enrich_memory', status: 'completed', durationLabel: '220ms', attempts: 1, meta: 'facts=3 entities=1' },
        { name: 'agent_reasoning', status: 'completed', durationLabel: '1.4s', attempts: 2, note: '1 retry due to timeout' },
        { name: 'validate_response', status: 'completed', durationLabel: '80ms', attempts: 1 },
        { name: 'persist_memory', status: 'completed', durationLabel: '180ms', attempts: 1 },
      ]
    : [
        { name: 'start', status: 'completed', durationLabel: '40ms', attempts: 1 },
        { name: 'process', status: 'running', durationLabel: '—', attempts: 1, meta: 'processing' },
      ]

  return {
    workflowId,
    workflowType: isAgent ? 'AgentWorkflow' : 'Workflow',
    status: 'completed',
    agentId: 'elena',
    sessionId: 'session-thread',
    traceId: '7c2d…',
    steps,
    contextSnapshot: [
      { k: 'Active agent', v: 'elena' },
      { k: 'Last user message', v: 'Why didn’t ingestion show up on gh-pages?' },
      { k: 'Retrieved facts', v: '3' },
      { k: 'Validation', v: 'PASS' },
    ],
  }
}
