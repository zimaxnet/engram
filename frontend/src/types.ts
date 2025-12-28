export type AgentId = 'elena' | 'marcus' | 'sage';

export interface Agent {
    id: AgentId;
    name: string;
    title: string;
    accentColor: string;
    avatarUrl: string;
    description?: string;
    voiceEnabled?: boolean;
}

export const AGENTS: Record<AgentId, Agent> = {
    elena: {
        id: 'elena',
        name: 'Dr. Elena Vasquez',
        title: 'Business Analyst',
        accentColor: '#3b82f6',
        avatarUrl: '/assets/images/elena-portrait.png',
        voiceEnabled: true
    },
    marcus: {
        id: 'marcus',
        name: 'Marcus Chen',
        title: 'Project Manager',
        accentColor: '#a855f7',
        avatarUrl: '/assets/images/marcus-portrait.png',
        voiceEnabled: false
    },
    sage: {
        id: 'sage',
        name: 'Sage Meridian',
        title: 'Storyteller',
        accentColor: '#f59e0b', // Amber/Gold for creativity
        avatarUrl: '/agents/sage-headshot.png',
        voiceEnabled: false
    }
};
