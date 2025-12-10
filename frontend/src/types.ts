export type AgentId = 'elena' | 'marcus';

export interface Agent {
    id: AgentId;
    name: string;
    title: string;
    accentColor: string;
    avatarUrl: string;
    description?: string;
}

export const AGENTS: Record<AgentId, Agent> = {
    elena: {
        id: 'elena',
        name: 'Dr. Elena Vasquez',
        title: 'Business Analyst',
        accentColor: '#3b82f6',
        avatarUrl: '/assets/images/elena-portrait.png'
    },
    marcus: {
        id: 'marcus',
        name: 'Marcus Chen',
        title: 'Project Manager',
        accentColor: '#a855f7',
        avatarUrl: '/assets/images/marcus-portrait.png'
    }
};
