"""
Zep Context Provider.

Wraps the existing ZepMemoryClient to provide semantic search capabilities
to the Virtual Context Store.
"""

from typing import Any, Dict, Optional, List
from backend.context.providers.base import BaseContextProvider
from backend.memory.client import memory_client

class ZepProvider(BaseContextProvider):
    """
    Provider for fetching context from Zep's Semantic Memory.
    """

    @property
    def provider_id(self) -> str:
        return "zep"

    async def fetch(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Fetch semantic context from Zep.
        
        Args:
            query: The search text (e.g. "project delta status")
            filters: Optional dictionary. Supported keys:
                     - session_id: Restrict search to specific session
                     - limit: Max results (default 5)
        
        Returns:
            List of memory chunks/facts.
        """
        session_id = filters.get("session_id", "global") if filters else "global"
        limit = filters.get("limit", 5) if filters else 5

        # Use the existing memory client logic
        # Note: If session_id is 'global', we might need a different Zep call (search across sessions),
        # but for now we assume session-scoped search or fallback.
        # Ideally, Zep supports cross-session search.
        
        # For this v1, we map "context query" -> "memory search"
        results = await memory_client.search_memory(
            session_id=session_id,
            query=query,
            limit=limit
        )
        return results

    async def health_check(self) -> bool:
        # Simple check: do we have a client?
        # A real check would ping Zep /health
        return memory_client.client is not None
