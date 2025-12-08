"""
Agent management endpoints

Provides API for:
- Listing available agents (Elena, Marcus)
- Getting agent details and capabilities
- Switching active agent
"""

from enum import Enum
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class AgentId(str, Enum):
    ELENA = "elena"
    MARCUS = "marcus"


class AgentProfile(BaseModel):
    id: AgentId
    name: str
    title: str
    expertise: list[str]
    personality_traits: list[str]
    voice_name: str
    accent_color: str
    avatar_url: Optional[str] = None
    is_available: bool = True


# Agent definitions
AGENTS: dict[AgentId, AgentProfile] = {
    AgentId.ELENA: AgentProfile(
        id=AgentId.ELENA,
        name="Dr. Elena Vasquez",
        title="Business Analyst",
        expertise=[
            "Requirements analysis",
            "Stakeholder management", 
            "Digital transformation",
            "Process optimization",
            "Compliance requirements"
        ],
        personality_traits=[
            "Analytical",
            "Empathetic",
            "Probing",
            "Synthesizing"
        ],
        voice_name="en-US-JennyNeural",
        accent_color="#3b82f6",  # Cyan
        avatar_url="/assets/images/elena-portrait.png"
    ),
    AgentId.MARCUS: AgentProfile(
        id=AgentId.MARCUS,
        name="Marcus Chen",
        title="Project Manager",
        expertise=[
            "Program management",
            "Agile transformation",
            "Risk mitigation",
            "Timeline planning",
            "Resource allocation"
        ],
        personality_traits=[
            "Pragmatic",
            "Direct",
            "Risk-aware",
            "Timeline-focused",
            "Team-oriented"
        ],
        voice_name="en-US-GuyNeural",
        accent_color="#a855f7",  # Purple
        avatar_url="/assets/images/marcus-portrait.png"
    ),
}


class AgentListResponse(BaseModel):
    agents: list[AgentProfile]
    active_agent: Optional[AgentId] = None


@router.get("", response_model=AgentListResponse)
async def list_agents():
    """List all available agents"""
    return AgentListResponse(
        agents=list(AGENTS.values()),
        active_agent=AgentId.ELENA  # Default
    )


@router.get("/{agent_id}", response_model=AgentProfile)
async def get_agent(agent_id: AgentId):
    """Get details for a specific agent"""
    if agent_id not in AGENTS:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return AGENTS[agent_id]


class SwitchAgentRequest(BaseModel):
    agent_id: AgentId


class SwitchAgentResponse(BaseModel):
    success: bool
    active_agent: AgentProfile
    message: str


@router.post("/switch", response_model=SwitchAgentResponse)
async def switch_agent(request: SwitchAgentRequest):
    """Switch the active agent for the current session"""
    if request.agent_id not in AGENTS:
        raise HTTPException(status_code=404, detail=f"Agent {request.agent_id} not found")
    
    agent = AGENTS[request.agent_id]
    
    return SwitchAgentResponse(
        success=True,
        active_agent=agent,
        message=f"Switched to {agent.name}. How can I help you today?"
    )

