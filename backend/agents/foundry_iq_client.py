"""
Azure AI Foundry IQ Client

Provides REST API client for Azure AI Foundry IQ (Knowledge Base Search).
Uses Azure AI Search for enterprise document search.

This is a POC implementation for enterprise document search.
All features are behind feature flags and disabled by default.
"""

import logging
from typing import Optional, List, Dict, Any
import httpx
from azure.core.credentials import TokenCredential
from azure.identity import DefaultAzureCredential

from backend.core import get_settings

logger = logging.getLogger(__name__)


class FoundryIQClient:
    """
    Client for Azure AI Foundry IQ (Knowledge Base Search).
    
    Provides enterprise document search via Azure AI Search.
    All operations are feature-flag controlled and non-breaking.
    """
    
    def __init__(
        self,
        endpoint: Optional[str] = None,
        project: Optional[str] = None,
        knowledge_base_id: Optional[str] = None,
        api_key: Optional[str] = None,
        api_version: str = "2025-11-15-preview",
        credential: Optional[TokenCredential] = None,
    ):
        """
        Initialize Foundry IQ client.
        
        Args:
            endpoint: Foundry endpoint (e.g., https://<account>.services.ai.azure.com)
            project: Foundry project name
            knowledge_base_id: Foundry IQ knowledge base ID
            api_key: Optional API key (falls back to Managed Identity if not provided)
            api_version: API version for Foundry IQ REST API
            credential: Optional TokenCredential (uses DefaultAzureCredential if not provided)
        """
        self.settings = get_settings()
        
        self.endpoint = endpoint or self.settings.azure_foundry_agent_endpoint
        self.project = project or self.settings.azure_foundry_agent_project
        self.knowledge_base_id = knowledge_base_id or self.settings.foundry_iq_knowledge_base_id
        self.api_key = api_key or self.settings.azure_foundry_agent_key
        self.api_version = api_version or self.settings.azure_foundry_agent_api_version
        
        # Use Managed Identity or API key
        if self.api_key:
            self.credential = None
            self.auth_mode = "api_key"
        else:
            self.credential = credential or DefaultAzureCredential()
            self.auth_mode = "bearer"
        
        # Build base URL for Foundry IQ APIs
        if not self.endpoint:
            raise ValueError("Azure AI Foundry endpoint not configured. Set AZURE_FOUNDRY_AGENT_ENDPOINT.")
        
        if not self.project:
            raise ValueError("Azure AI Foundry project not configured. Set AZURE_FOUNDRY_AGENT_PROJECT.")
        
        if not self.knowledge_base_id:
            raise ValueError("Foundry IQ knowledge base ID not configured. Set FOUNDRY_IQ_KB_ID.")
        
        base = self.endpoint.rstrip("/")
        self.base_url = f"{base}/api/projects/{self.project}/knowledge-bases/{self.knowledge_base_id}"
        
        logger.info(f"FoundryIQClient initialized: endpoint={self.endpoint}, project={self.project}, kb_id={self.knowledge_base_id}")
    
    async def _get_headers(self) -> dict:
        """Get authentication headers for API requests."""
        headers = {
            "Content-Type": "application/json",
        }
        
        if self.auth_mode == "api_key":
            headers["api-key"] = self.api_key
        elif self.auth_mode == "bearer":
            # Foundry requires audience: https://ai.azure.com
            token = self.credential.get_token("https://ai.azure.com/.default")
            headers["Authorization"] = f"Bearer {token.token}"
        
        return headers
    
    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        project_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search the Foundry IQ knowledge base.
        
        Args:
            query: Search query text
            limit: Maximum number of results to return
            filters: Optional filters (source, date_range, etc.)
            project_id: Optional project ID for scoping
            
        Returns:
            List of search results with content, source, score, metadata
        """
        url = f"{self.base_url}/search"
        headers = await self._get_headers()
        
        payload = {
            "query": query,
            "top": limit,
        }
        
        if filters:
            payload["filters"] = filters
        
        if project_id:
            payload["project_id"] = project_id
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                    params={"api-version": self.api_version},
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract results from response
                results = data.get("results", [])
                
                # Transform to Engram-compatible format
                transformed_results = []
                for result in results:
                    transformed_results.append({
                        "content": result.get("content", ""),
                        "source": result.get("source", "foundry-iq"),
                        "score": result.get("score", 0.0),
                        "metadata": {
                            **result.get("metadata", {}),
                            "foundry_iq": True,
                            "knowledge_base_id": self.knowledge_base_id,
                        },
                    })
                
                logger.info(f"Foundry IQ search returned {len(transformed_results)} results for query: {query[:50]}")
                return transformed_results
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Foundry IQ search failed: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error searching Foundry IQ: {e}", exc_info=True)
            raise
    
    async def list_knowledge_bases(self) -> List[Dict[str, Any]]:
        """
        List all knowledge bases in the project.
        
        Returns:
            List of knowledge base information
        """
        url = f"{self.endpoint.rstrip('/')}/api/projects/{self.project}/knowledge-bases"
        headers = await self._get_headers()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    headers=headers,
                    params={"api-version": self.api_version},
                )
                response.raise_for_status()
                data = response.json()
                
                knowledge_bases = data.get("value", []) if isinstance(data, dict) else data
                logger.info(f"Listed {len(knowledge_bases)} knowledge bases")
                return knowledge_bases
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to list knowledge bases: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error listing knowledge bases: {e}")
            raise
    
    async def get_knowledge_base(self, knowledge_base_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about a specific knowledge base.
        
        Args:
            knowledge_base_id: Knowledge base ID (uses instance default if not provided)
            
        Returns:
            Knowledge base information
        """
        kb_id = knowledge_base_id or self.knowledge_base_id
        url = f"{self.endpoint.rstrip('/')}/api/projects/{self.project}/knowledge-bases/{kb_id}"
        headers = await self._get_headers()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    headers=headers,
                    params={"api-version": self.api_version},
                )
                response.raise_for_status()
                data = response.json()
                
                logger.info(f"Retrieved knowledge base: {kb_id}")
                return data
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get knowledge base: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error getting knowledge base: {e}")
            raise


# Singleton instance (lazy-loaded)
_foundry_iq_client: Optional[FoundryIQClient] = None


def get_foundry_iq_client() -> Optional[FoundryIQClient]:
    """
    Get or create Foundry IQ client singleton.
    
    Returns None if Foundry IQ is not configured (feature flags disabled).
    This ensures zero impact when Foundry IQ is not in use.
    """
    global _foundry_iq_client
    
    settings = get_settings()
    
    # Only create client if Foundry IQ is enabled and configured
    if not settings.use_foundry_iq:
        return None
    
    if not settings.azure_foundry_agent_endpoint or not settings.azure_foundry_agent_project:
        return None
    
    if not settings.foundry_iq_knowledge_base_id:
        logger.warning("Foundry IQ enabled but knowledge base ID not configured. Set FOUNDRY_IQ_KB_ID.")
        return None
    
    if _foundry_iq_client is None:
        try:
            _foundry_iq_client = FoundryIQClient()
            logger.info("Foundry IQ client initialized")
        except (ValueError, Exception) as e:
            logger.warning(f"Foundry IQ client initialization failed (non-blocking): {e}")
            return None
    
    return _foundry_iq_client

