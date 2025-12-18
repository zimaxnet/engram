"""
Virtual Context Store (Orchestrator).

This module is the "Brain" that resolves Context Requests.
It connects the Registry (Definitions) with the Providers (Data).
"""

import logging
from typing import Any, Dict, Optional
from backend.context.registry import ContextRegistry
from backend.context.providers.zep import ZepProvider

logger = logging.getLogger(__name__)

class VirtualContextStore:
    """
    The main entry point for Agents to request context.
    """
    
    def __init__(self):
        self.providers = {
            "zep": ZepProvider()
            # "postgres": PostgresProvider() (Future)
        }

    async def get_context(self, context_name: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Resolve and fetch a named context.

        Args:
            context_name: The name of the registered context (e.g. "user_profile")
            params: Arguments to pass to the context function (e.g. {"user_id": "123"})

        Returns:
            The resolved context data (dict, object, or list)
        """
        definition = ContextRegistry.get(context_name)
        if not definition:
            logger.warning(f"Context '{context_name}' not found in registry.")
            return None

        params = params or {}
        
        try:
            # 1. If it has a bound python function, execute it
            # This is "Context-as-Code"
            if definition.func:
                # We assume the function is async if it calls providers, 
                # but for simplicity let's handle both or assume async.
                # For now, let's assume standard sync execution or await if native.
                # To be robust, we'd check inspect.iscoroutinefunction(definition.func)
                
                # In this V1, let's assume the function *calls* the store back or uses providers directly.
                # OR, the function *is* the logic.
                
                # Simple injection: pass params as functional args
                import inspect
                if inspect.iscoroutinefunction(definition.func):
                    return await definition.func(**params)
                else:
                    return definition.func(**params)

            # 2. If it's a direct provider mapping (declarative, no code)
            elif definition.provider_type:
                provider = self.providers.get(definition.provider_type)
                if not provider:
                    raise ValueError(f"Provider '{definition.provider_type}' not configured.")
                
                # For declarative, we assume 'params' contains the query
                query = params.get("query", "")
                return await provider.fetch(query=query, filters=params)

        except Exception as e:
            logger.error(f"Error resolving context '{context_name}': {e}")
            raise

# Singleton
store = VirtualContextStore()
