export interface BauFlow {
  id: 'intake-triage' | 'policy-qa' | 'decision-log'
  title: string
  persona: string
  description: string
  cta: string
}

export interface BauArtifact {
  id: string
  name: string
  ingestedLabel: string
  chips: string[]
}

export async function listBauFlows(): Promise<BauFlow[]> {
  return [
    {
      id: 'intake-triage',
      title: 'Intake & triage',
      persona: 'Marcus',
      description: 'Turn requests into plans, milestones, owners, and risk flags.',
      cta: 'Start',
    },
    {
      id: 'policy-qa',
      title: 'Policy Q&A',
      persona: 'Elena',
      description: 'Ask questions and get answers with citations and sensitivity warnings.',
      cta: 'Ask',
    },
    {
      id: 'decision-log',
      title: 'Decision log search',
      persona: 'Elena + Marcus',
      description: 'Recall decisions and provenance across time and projects.',
      cta: 'Search',
    },
  ]
}

export async function listRecentArtifacts(): Promise<BauArtifact[]> {
  return [
    {
      id: 'art-1',
      name: 'Meeting notes — Steering Committee',
      ingestedLabel: 'ingested 2h ago',
      chips: ['tenant:zimax', 'project:alpha', 'sensitivity:silver'],
    },
    {
      id: 'art-2',
      name: 'Policy update — Data retention',
      ingestedLabel: 'ingested 1d ago',
      chips: ['tenant:zimax', 'domain:security', 'sensitivity:gold'],
    },
  ]
}
