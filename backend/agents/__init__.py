"""
Engram Agent Module

Contains LangGraph agent implementations for Elena, Marcus, and Sage,
plus the router for agent selection and handoffs.
"""

from .base import AgentState, BaseAgent
from .elena import ElenaAgent, elena
from .marcus import MarcusAgent, marcus
from .sage import SageAgent, sage
from .router import AgentRouter, chat, get_agent, router

__all__ = [
    # Base
    "BaseAgent",
    "AgentState",
    # Elena
    "ElenaAgent",
    "elena",
    # Marcus
    "MarcusAgent",
    "marcus",
    # Sage
    "SageAgent",
    "sage",
    # Router
    "AgentRouter",
    "router",
    "get_agent",
    "chat",
]

