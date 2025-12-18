"""
Abstract Base Class for Context Providers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseContextProvider(ABC):
    """
    Interface that all Physical Context Providers must implement.
    Examples: ZepProvider, PostgresProvider, SharePointProvider.
    """

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Unique identifier for this provider type (e.g., 'zep')"""
        pass

    @abstractmethod
    async def fetch(self, query: str, filters: Optional[Dict[str, Any]] = None) -> Any:
        """
        Fetch data from the provider.
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Return True if provider is reachable.
        """
        pass
