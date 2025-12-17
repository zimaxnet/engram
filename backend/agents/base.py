"""
Base Agent Module

Provides the foundation for all Engram agents using LangGraph.
Implements the Brain layer of the Brain + Spine architecture.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Literal, Optional, TypedDict

from azure.core.credentials import TokenCredential
from azure.identity import DefaultAzureCredential

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
    """Minimal async chat client for OpenAI-compatible API (Azure API Gateway)."""

    def __init__(
        self,
        *,
        endpoint: str,
        deployment: str,
        api_version: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        timeout: float = 60.0,
        api_key: Optional[str] = None,
        credential: Optional[TokenCredential] = None,
        scope: str = "https://cognitiveservices.azure.com/.default",
    ) -> None:
        # Support OpenAI-compatible endpoint format
        base = endpoint.rstrip("/")
        # Check if this is an OpenAI-compatible endpoint (contains /openai/v1 or similar)
        if "/openai/v1" in base or base.endswith("/v1"):
            # OpenAI-compatible format: endpoint already includes the path
            self.url = f"{base}/chat/completions"
            self.is_openai_compat = True
            self.model = deployment  # Use model parameter instead of deployment path
        else:
            # Azure AI Foundry format
            self.url = f"{base}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"
            self.model = None
            self.is_openai_compat = False
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.credential = credential
        self.scope = scope

        # Determine auth mode
        if api_key:
            self.auth_mode = "api_key"
        elif credential:
            self.auth_mode = "bearer"
        else:
            raise ValueError("Provide azure_ai_key or a TokenCredential (DefaultAzureCredential) for authentication.")

        # Base headers (Authorization added per request when using bearer)
        self.base_headers = {"Content-Type": "application/json"}

        if self.auth_mode == "api_key":
            if self.is_openai_compat:
                # APIM/OpenAI-compatible endpoints often expect either header name
                self.base_headers.update({
                    "Ocp-Apim-Subscription-Key": api_key,
                    "api-key": api_key,
                })
            else:
                self.base_headers.update({"api-key": api_key})

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
        import logging
        logger = logging.getLogger(__name__)
        
        payload = {
            "messages": [self._format_message(m) for m in messages],
        }
        # Add model for OpenAI-compatible endpoints
        if self.is_openai_compat and self.model:
            payload["model"] = self.model
        
        # Only add temperature and max_tokens for non-OpenAI-compat endpoints
        # (some models like gpt-5.1-chat don't support custom temperature)
        if not self.is_openai_compat:
            payload["temperature"] = self.temperature
            payload["max_tokens"] = self.max_tokens

        logger.info(f"FoundryChatClient: Calling {self.url}")
        logger.info(f"FoundryChatClient: is_openai_compat={self.is_openai_compat}, model={self.model}")
        
        # Compute headers for this request (add bearer token if using managed identity)
        headers = dict(self.base_headers)
        if self.credential:
            token = self.credential.get_token(self.scope)
            headers["Authorization"] = f"Bearer {token.token}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(self.url, headers=headers, json=payload)
                logger.info(f"FoundryChatClient: Response status={response.status_code}")
                response.raise_for_status()
            except Exception as e:
                logger.error(f"FoundryChatClient: Error calling LLM: {e}")
                raise
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
        """Lazy-load the chat client (OpenAI-compatible or Azure AI Foundry)."""
        if self._llm is None:
            endpoint = self.settings.azure_ai_endpoint
            if not endpoint:
                raise ValueError("Azure AI endpoint not configured. Set AZURE_AI_ENDPOINT.")

            # Only add project path for Azure AI Foundry endpoints (not Azure OpenAI or APIM)
            # Azure OpenAI: *.openai.azure.com
            # APIM Gateway: contains /openai/v1
            # Azure AI Foundry: *.services.ai.azure.com (needs project path)
            is_azure_openai = "openai.azure.com" in endpoint
            is_apim_gateway = "/openai/v1" in endpoint
            
            if self.settings.azure_ai_project_name and not is_azure_openai and not is_apim_gateway:
                endpoint = f"{endpoint.rstrip('/')}/api/projects/{self.settings.azure_ai_project_name}"

            # Prefer managed identity (DefaultAzureCredential) when no API key is supplied
            credential: Optional[TokenCredential] = None
            api_key: Optional[str] = self.settings.azure_ai_key
            if not api_key:
                credential = DefaultAzureCredential()

            self._llm = FoundryChatClient(
                endpoint=endpoint,
                deployment=self.settings.azure_ai_deployment,
                api_version=self.settings.azure_ai_api_version,
                temperature=0.7,
                max_tokens=4096,
                api_key=api_key,
                credential=credential,
                scope="https://cognitiveservices.azure.com/.default",
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

    async def run(self, user_message: str, context: EnterpriseContext) -> tuple[str, EnterpriseContext]:
        """
        Execute the agent with a user message.

        Args:
            user_message: The user's input
            context: The current enterprise context

        Returns:
            Tuple of (response_text, updated_context)
        """
        # Add user message to context
        user_turn = Turn(role=MessageRole.USER, content=user_message, timestamp=datetime.utcnow())
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
        response = final_state.get("final_response", "I apologize, but I couldn't generate a response.")

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
        return f"<{self.__class__.__name__}(id={self.agent_id}, name={self.agent_name})>"
