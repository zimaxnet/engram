"""
Context Registry (Context-as-Code)

This module defines the mechanism for registering and retrieving Context Definitions.
Context Definitions are declaratively defined using the `@register_context` decorator.
"""

from typing import Callable, Any, Dict, Optional, List
from pydantic import BaseModel, Field, ConfigDict
import inspect


from typing import Callable, Any, Dict, Optional, List
from pydantic import BaseModel, Field
import inspect


class ContextDefinition(BaseModel):
    """
    Metadata about a Context Definition.
    
    A Context Definition is a named logic block (function) that knows how to
    fetch and assemble a specific set of information (context) for an Agent.
    """
    name: str = Field(..., description="Unique name of the context (e.g., 'project_status')")
    description: str = Field("", description="Human-readable description of what this context provides")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters this context function accepts")
    provider_type: Optional[str] = Field(None, description="The backing provider type (e.g., 'zep', 'postgres')")
    func: Optional[Callable] = Field(None, exclude=True, description="The actual python function to execute")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ContextRegistry:
    """
    Singleton registry to hold all registered context definitions.
    """
    _registry: Dict[str, ContextDefinition] = {}

    @classmethod
    def register(cls, definition: ContextDefinition):
        if definition.name in cls._registry:
            # warn or overwrite? adhering to "last one wins" for reloadability
            pass
        cls._registry[definition.name] = definition

    @classmethod
    def get(cls, name: str) -> Optional[ContextDefinition]:
        return cls._registry.get(name)

    @classmethod
    def list(cls) -> List[ContextDefinition]:
        return list(cls._registry.values())


def register_context(name: str, description: str = "", provider_type: str = "custom"):
    """
    Decorator to register a function as a Context Provider.

    Usage:
        @register_context(name="user_profile", description="Basic user details")
        def get_user_profile(user_id: str):
            ...
    """
    def decorator(func: Callable):
        # Introspect function signature for parameters
        sig = inspect.signature(func)
        params = {}
        for param_name, param in sig.parameters.items():
            if param_name in ["self", "cls"]:
                continue
            params[param_name] = str(param.annotation)

        definition = ContextDefinition(
            name=name,
            description=description,
            parameters=params,
            provider_type=provider_type,
            func=func
        )
        ContextRegistry.register(definition)
        return func
    return decorator

# --- Built-in Engram Self-Reflection Contexts ---
# These allow the system to answer questions about its own state.

@register_context(name="engram_project_state", description="High-level status of the Engram project implementation")
async def get_engram_status(query_focus: str = "general"):
    """
    Fetches the current status of the Engram project itself by querying the Virtual Context Store.
    
    This is the Recursive Context mechanism: Engram reading its own memory to understand its state.
    """
    # Self-Query: Ask Zep about "Engram Implementation Plan" and "Java Research"
    # We use the store to resolve the 'zep' provider.
    
    # 1. Fetch relevant facts from Zep (The Knowledge Graph)
    from backend.context.store import store
    zep = store.providers["zep"]
    
    # Query for distinct topics
    plan_facts = await zep.fetch(query="Engram Virtual Context Store implementation")
    research_facts = await zep.fetch(query="MCP Java SDK Research")
    
    return {
        "project": "Engram",
        "focus": query_focus,
        "implementation_status": [f["content"] for f in plan_facts if "content" in f],
        "research_findings": [f["content"] for f in research_facts if "content" in f],
        "meta": "Recursive Context: Retrieved from Engram's own Knowledge Graph."
    }

