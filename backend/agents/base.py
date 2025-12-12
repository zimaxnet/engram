"""
Base Agent Module

Provides the foundation for all Engram agents using LangGraph.
Implements the Brain layer of the Brain + Spine architecture.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Literal, Optional, TypedDict

import httpx
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from backend.core import EnterpriseContext, MessageRole, Turn, get_settings


class AgentState(TypedDict):
    """State passed through the LangGraph agent"""

    messages: list[BaseMessage]
    context: EnterpriseContext
    current_step: str
    should_continue: bool
    tool_results: list[dict]
    final_response: Optional[str]


class FoundryChatClient:
    """Minimal async chat client for Azure AI Foundry (key auth)."""

    def __init__(
        self,
        *,
        endpoint: str,
        api_key: str,
        deployment: str,
        api_version: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        timeout: float = 60.0,
    ) -> None:
        base = endpoint.rstrip("/")
        self.url = (
            f"{base}/openai/deployments/{deployment}/chat/completions"
            f"?api-version={api_version}"
        )
        self.headers = {"api-key": api_key, "Content-Type": "application/json"}
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

    @staticmethod
    def _format_message(message: BaseMessage) -> dict:
        role_map = {
            "system": "system",
            "human": "user",
            "ai": "assistant",
            "assistant": "assistant",
        }
        role = role_map.get(message.type, "user")
        return {"role": role, "content": message.content}

    async def ainvoke(self, messages: list[BaseMessage]) -> AIMessage:
        payload = {
            "messages": [self._format_message(m) for m in messages],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.url, headers=self.headers, json=payload
            )
            response.raise_for_status()
            data = response.json()

        choice = data.get("choices", [{}])[0]
        msg = choice.get("message", {})
        content = msg.get("content", "")
        return AIMessage(content=content or "")


class BaseAgent(ABC):
    """
    Abstract base class for Engram agents.

    Each agent (Elena, Marcus) extends this class with their
    specific persona, expertise, and tools.
    """

    # Agent identity - override in subclasses
    agent_id: str = "base"
    agent_name: str = "Base Agent"
    agent_title: str = "Agent"

    def __init__(self):
        self.settings = get_settings()
        self._llm: Optional[FoundryChatClient] = None
        self._graph: Optional[StateGraph] = None

    @property
    def llm(self) -> FoundryChatClient:
        """Lazy-load the Azure AI Foundry client."""
        if self._llm is None:
            endpoint = self.settings.azure_ai_endpoint
            if self.settings.azure_ai_project_name:
                endpoint = f"{endpoint.rstrip('/')}/api/projects/{self.settings.azure_ai_project_name}"
            if not endpoint:
                raise ValueError(
                    "Azure AI endpoint not configured. Set AZURE_AI_ENDPOINT."
                )

            if not self.settings.azure_ai_key:
                raise ValueError("Azure AI API key not configured")

            self._llm = FoundryChatClient(
                endpoint=endpoint,
                api_key=self.settings.azure_ai_key,
                deployment=self.settings.azure_ai_deployment,
                api_version=self.settings.azure_ai_api_version,
                temperature=0.7,
                max_tokens=4096,
            )
        return self._llm

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """
        The system prompt that defines the agent's persona.
        Must be implemented by each agent subclass.
        """
        pass

    @property
    def tools(self) -> list:
        """
        Tools available to this agent.
        Override in subclasses to add agent-specific tools.
        """
        return []

    def build_graph(self) -> StateGraph:
        """
        Build the LangGraph state machine for this agent.

        Default implementation provides a simple:
        reason -> respond flow.

        Override for more complex agent logic.
        """
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("reason", self._reason_node)
        workflow.add_node("respond", self._respond_node)

        # Add edges
        workflow.set_entry_point("reason")
        workflow.add_conditional_edges(
            "reason",
            self._should_continue,
            {
                "continue": "reason",
                "respond": "respond",
            },
        )
        workflow.add_edge("respond", END)

        return workflow.compile()

    @property
    def graph(self):
        """Lazy-load the compiled graph"""
        if self._graph is None:
            self._graph = self.build_graph()
        return self._graph

    async def _reason_node(self, state: AgentState) -> AgentState:
        """
        The reasoning node - processes input and decides next action.
        """
        # Build messages with system prompt and context
        messages = [
            SystemMessage(content=self._build_full_prompt(state["context"])),
            *state["messages"],
        ]

        # Call LLM
        response = await self.llm.ainvoke(messages)

        # Update state
        state["messages"].append(response)
        state["current_step"] = "reason"

        # Check if we need to use tools or can respond
        # For now, simple implementation - always respond after reasoning
        state["should_continue"] = False
        state["final_response"] = response.content

        return state

    async def _respond_node(self, state: AgentState) -> AgentState:
        """
        The response node - formats the final response.
        """
        state["current_step"] = "respond"
        return state

    def _should_continue(self, state: AgentState) -> Literal["continue", "respond"]:
        """
        Determine if the agent should continue reasoning or respond.
        """
        if state["should_continue"]:
            return "continue"
        return "respond"

    def _build_full_prompt(self, context: EnterpriseContext) -> str:
        """
        Build the complete system prompt including:
        - Agent persona
        - User context
        - Retrieved knowledge
        - Current plan (if any)
        """
        parts = [self.system_prompt, "", "---", "", context.to_llm_context()]
        return "\n".join(parts)

    async def run(
        self, user_message: str, context: EnterpriseContext
    ) -> tuple[str, EnterpriseContext]:
        """
        Execute the agent with a user message.

        Args:
            user_message: The user's input
            context: The current enterprise context

        Returns:
            Tuple of (response_text, updated_context)
        """
        # Add user message to context
        user_turn = Turn(
            role=MessageRole.USER, content=user_message, timestamp=datetime.utcnow()
        )
        context.episodic.add_turn(user_turn)

        # Build initial state
        initial_state: AgentState = {
            "messages": [HumanMessage(content=user_message)],
            "context": context,
            "current_step": "start",
            "should_continue": True,
            "tool_results": [],
            "final_response": None,
        }

        # Run the graph
        final_state = await self.graph.ainvoke(initial_state)

        # Extract response
        response = final_state.get(
            "final_response", "I apologize, but I couldn't generate a response."
        )

        # Add assistant turn to context
        assistant_turn = Turn(
            role=MessageRole.ASSISTANT,
            content=response,
            timestamp=datetime.utcnow(),
            agent_id=self.agent_id,
        )
        context.episodic.add_turn(assistant_turn)
        context.update_timestamp()

        # Update operational state
        context.operational.total_llm_calls += 1

        return response, context

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__}(id={self.agent_id}, name={self.agent_name})>"
        )
