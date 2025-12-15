import { listBauFlows as apiListBauFlows, listBauArtifacts as apiListBauArtifacts } from './api'

export interface BauFlow {
  id: string
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

function formatIngestedLabel(ingestedAt: string): string {
  const date = new Date(ingestedAt)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffHours / 24)

  if (diffDays > 0) {
    return `ingested ${diffDays}d ago`
  } else if (diffHours > 0) {
    return `ingested ${diffHours}h ago`
  } else {
    const diffMins = Math.floor(diffMs / (1000 * 60))
    return `ingested ${diffMins}m ago`
  }
}

export async function listBauFlows(): Promise<BauFlow[]> {
  return apiListBauFlows()
}

export async function listRecentArtifacts(): Promise<BauArtifact[]> {
  const artifacts = await apiListBauArtifacts(20)
  return artifacts.map((a) => ({
    id: a.id,
    name: a.name,
    ingestedLabel: formatIngestedLabel(a.ingested_at),
    chips: a.chips,
  }))
}
