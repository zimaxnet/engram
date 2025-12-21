"""
Agent Router

Routes requests to the appropriate agent (Elena or Marcus) based on:
1. Explicit user selection
2. Conversation context
3. Query content analysis

Also handles agent handoffs when one agent recommends the other.
"""

import re
from typing import Literal, Optional

from backend.core import EnterpriseContext

from .base import BaseAgent
from .elena import elena
from .marcus import marcus
from .sage import sage


AgentId = Literal["elena", "marcus", "sage"]


class AgentRouter:
    """
    Routes requests to the appropriate agent and manages handoffs.
    """

    def __init__(self):
        self.agents: dict[AgentId, BaseAgent] = {
            "elena": elena,
            "marcus": marcus,
            "sage": sage,
        }

        # Keywords that suggest routing to specific agents
        self._elena_keywords = {
            "requirement",
            "requirements",
            "stakeholder",
            "stakeholders",
            "business",
            "analysis",
            "analyze",
            "user story",
            "stories",
            "acceptance criteria",
            "scope",
            "compliance",
            "regulation",
            "process",
            "workflow",
            "documentation",
            "specification",
        }

        self._marcus_keywords = {
            "project",
            "timeline",
            "schedule",
            "deadline",
            "sprint",
            "velocity",
            "estimation",
            "estimate",
            "risk",
            "risks",
            "blocker",
            "blocked",
            "resource",
            "resources",
            "budget",
            "milestone",
            "delivery",
            "shipped",
            "launch",
            "release",
        }

        self._sage_keywords = {
            "story",
            "storytelling",
            "narrative",
            "diagram",
            "visualization",
            "visualize",
            "document",
            "documentation",
            "explain",
            "presentation",
            "write",
        }

    def get_agent(self, agent_id: AgentId) -> BaseAgent:
        """Get a specific agent by ID"""
        if agent_id not in self.agents:
            raise ValueError(f"Unknown agent: {agent_id}")
        return self.agents[agent_id]

    def suggest_agent(self, query: str, current_agent: Optional[AgentId] = None) -> AgentId:
        """
        Suggest the best agent for a query based on content analysis.

        Args:
            query: The user's query text
            current_agent: The currently active agent (for continuity preference)

        Returns:
            Suggested agent ID
        """
        query_lower = query.lower()

        # Count keyword matches
        elena_score = sum(1 for kw in self._elena_keywords if kw in query_lower)
        marcus_score = sum(1 for kw in self._marcus_keywords if kw in query_lower)
        sage_score = sum(1 for kw in self._sage_keywords if kw in query_lower)

        # Add continuity bonus if there's a current agent
        if current_agent:
            if current_agent == "elena":
                elena_score += 0.5
            elif current_agent == "marcus":
                marcus_score += 0.5
            else:
                sage_score += 0.5

        # Return agent with higher score, default to elena
        scores = {"elena": elena_score, "marcus": marcus_score, "sage": sage_score}
        best_agent = max(scores, key=scores.get)
        if scores[best_agent] > 0:
            return best_agent
        return "elena"

    def detect_handoff(self, response: str) -> Optional[AgentId]:
        """
        Detect if an agent response suggests handing off to the other agent.

        Args:
            response: The agent's response text

        Returns:
            Target agent ID if handoff detected, None otherwise
        """
        response_lower = response.lower()

        # Patterns suggesting handoff to Marcus
        marcus_handoff_patterns = [
            r"marcus (can|could|would|should) help",
            r"hand.*(off|over).*marcus",
            r"project manager.*perspective",
            r"timeline.*estimation",
            r"marcus.*better suited",
        ]

        # Patterns suggesting handoff to Elena
        elena_handoff_patterns = [
            r"elena (can|could|would|should) help",
            r"hand.*(off|over).*elena",
            r"business analyst.*perspective",
            r"requirements.*analysis",
            r"elena.*better suited",
        ]

        for pattern in marcus_handoff_patterns:
            if re.search(pattern, response_lower):
                return "marcus"

        for pattern in elena_handoff_patterns:
            if re.search(pattern, response_lower):
                return "elena"

        return None

    async def route_and_execute(
        self, query: str, context: EnterpriseContext, agent_id: Optional[AgentId] = None
    ) -> tuple[str, EnterpriseContext, AgentId]:
        """
        Route query to appropriate agent and execute.

        Args:
            query: User's query
            context: Current enterprise context
            agent_id: Explicit agent selection (optional)

        Returns:
            Tuple of (response, updated_context, agent_id_used)
        """
        # Determine which agent to use
        if agent_id:
            selected_agent_id = agent_id
        else:
            current = context.operational.active_agent
            selected_agent_id = self.suggest_agent(query, current)

        # Update context with active agent
        context.operational.active_agent = selected_agent_id

        # Get agent and execute
        agent = self.get_agent(selected_agent_id)
        response, updated_context = await agent.run(query, context)

        # Check for handoff suggestion
        handoff_target = self.detect_handoff(response)
        if handoff_target and handoff_target != selected_agent_id:
            # Add handoff note to response
            target_agent = self.get_agent(handoff_target)
            response += f"\n\n*[{target_agent.agent_name} is available if you'd like their perspective.]*"

        return response, updated_context, selected_agent_id

    def get_agent_info(self, agent_id: AgentId) -> dict:
        """Get information about an agent for the UI"""
        agent = self.get_agent(agent_id)
        return {
            "id": agent.agent_id,
            "name": agent.agent_name,
            "title": agent.agent_title,
            "tools": [t.name for t in agent.tools] if agent.tools else [],
        }

    def list_agents(self) -> list[dict]:
        """List all available agents"""
        return [self.get_agent_info(aid) for aid in self.agents.keys()]


# Singleton router instance
router = AgentRouter()


# Convenience functions
def get_agent(agent_id: AgentId) -> BaseAgent:
    """Get an agent by ID"""
    return router.get_agent(agent_id)


async def chat(
    query: str, context: EnterpriseContext, agent_id: Optional[AgentId] = None
) -> tuple[str, EnterpriseContext, AgentId]:
    """
    Main entry point for chatting with agents.

    Args:
        query: User's message
        context: Enterprise context
        agent_id: Optional explicit agent selection

    Returns:
        Tuple of (response, updated_context, agent_id_used)
    """
    return await router.route_and_execute(query, context, agent_id)
