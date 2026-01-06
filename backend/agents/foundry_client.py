"""
Azure AI Foundry Agent Service Client

Provides REST API client for Azure AI Foundry Agent Service.
Uses REST API directly (no SDK dependency) for maximum flexibility.

This is a POC implementation for thread management and file storage.
All features are behind feature flags and disabled by default.
"""

import logging
from typing import Optional
import httpx
from azure.core.credentials import TokenCredential
from azure.identity import DefaultAzureCredential

from backend.core import get_settings

logger = logging.getLogger(__name__)


class FoundryAgentServiceClient:
    """
    Client for Azure AI Foundry Agent Service using REST API.
    
    Provides thread management, file storage, and optional vector store operations.
    All operations are feature-flag controlled and non-breaking.
    """
    
    def __init__(
        self,
        endpoint: Optional[str] = None,
        project: Optional[str] = None,
        api_key: Optional[str] = None,
        api_version: str = "2025-11-15-preview",
        credential: Optional[TokenCredential] = None,
    ):
        """
        Initialize Foundry Agent Service client.
        
        Args:
            endpoint: Foundry Agent Service endpoint (e.g., https://<account>.services.ai.azure.com)
            project: Foundry project name
            api_key: Optional API key (falls back to Managed Identity if not provided)
            api_version: API version for Agent Service REST API
            credential: Optional TokenCredential (uses DefaultAzureCredential if not provided)
        """
        self.settings = get_settings()
        
        self.endpoint = endpoint or self.settings.azure_foundry_agent_endpoint
        self.project = project or self.settings.azure_foundry_agent_project
        self.api_key = api_key or self.settings.azure_foundry_agent_key
        self.api_version = api_version or self.settings.azure_foundry_agent_api_version
        
        # Use Managed Identity or API key
        if self.api_key:
            self.credential = None
            self.auth_mode = "api_key"
        else:
            self.credential = credential or DefaultAzureCredential()
            self.auth_mode = "bearer"
        
        # Build base URL for Agent Service APIs
        if not self.endpoint:
            raise ValueError("Azure AI Foundry Agent Service endpoint not configured. Set AZURE_FOUNDRY_AGENT_ENDPOINT.")
        
        if not self.project:
            raise ValueError("Azure AI Foundry Agent Service project not configured. Set AZURE_FOUNDRY_AGENT_PROJECT.")
        
        base = self.endpoint.rstrip("/")
        self.base_url = f"{base}/api/projects/{self.project}"
        
        logger.info(f"FoundryAgentServiceClient initialized: endpoint={self.endpoint}, project={self.project}")
    
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
    
    async def create_thread(
        self,
        user_id: str,
        agent_id: str,
        project_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Create a new conversation thread in Foundry Agent Service.
        
        Args:
            user_id: User identifier
            agent_id: Agent identifier (elena, marcus, sage)
            project_id: Optional project identifier for project-based isolation
            metadata: Optional additional metadata
            
        Returns:
            Thread ID (string)
        """
        url = f"{self.base_url}/threads"
        headers = await self._get_headers()
        
        thread_metadata = {
            "user_id": user_id,
            "agent_id": agent_id,
            "project_id": project_id or "default",
        }
        
        if metadata:
            thread_metadata.update(metadata)
        
        payload = {
            "metadata": thread_metadata,
        }
        
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
                thread_id = data.get("id")
                
                if not thread_id:
                    raise ValueError(f"Thread creation response missing 'id': {data}")
                
                logger.info(f"Created Foundry thread: {thread_id} for user={user_id}, agent={agent_id}, project={project_id}")
                return thread_id
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to create Foundry thread: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error creating Foundry thread: {e}")
            raise
    
    async def get_thread(self, thread_id: str) -> dict:
        """
        Get thread details from Foundry Agent Service.
        
        Args:
            thread_id: Thread identifier
            
        Returns:
            Thread details (dict)
        """
        url = f"{self.base_url}/threads/{thread_id}"
        headers = await self._get_headers()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    headers=headers,
                    params={"api-version": self.api_version},
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get Foundry thread: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error getting Foundry thread: {e}")
            raise
    
    async def list_threads(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict]:
        """
        List threads filtered by user, agent, and/or project.
        
        Args:
            user_id: Optional user identifier filter
            agent_id: Optional agent identifier filter
            project_id: Optional project identifier filter
            limit: Maximum number of threads to return
            
        Returns:
            List of thread dictionaries
        """
        url = f"{self.base_url}/threads"
        headers = await self._get_headers()
        
        params = {
            "api-version": self.api_version,
            "limit": limit,
        }
        
        # Note: Foundry API may support filtering via query params or metadata
        # Adjust based on actual API documentation
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    headers=headers,
                    params=params,
                )
                response.raise_for_status()
                data = response.json()
                
                threads = data.get("data", []) if isinstance(data, dict) else data
                
                # Client-side filtering if API doesn't support it
                if user_id or agent_id or project_id:
                    filtered = []
                    for thread in threads:
                        metadata = thread.get("metadata", {})
                        if user_id and metadata.get("user_id") != user_id:
                            continue
                        if agent_id and metadata.get("agent_id") != agent_id:
                            continue
                        if project_id and metadata.get("project_id") != project_id:
                            continue
                        filtered.append(thread)
                    threads = filtered
                
                logger.info(f"Listed {len(threads)} Foundry threads (filters: user={user_id}, agent={agent_id}, project={project_id})")
                return threads
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to list Foundry threads: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error listing Foundry threads: {e}")
            raise
    
    async def add_message(
        self,
        thread_id: str,
        role: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        Add a message to a thread.
        
        Args:
            thread_id: Thread identifier
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional message metadata
            
        Returns:
            Message details (dict)
        """
        url = f"{self.base_url}/threads/{thread_id}/messages"
        headers = await self._get_headers()
        
        payload = {
            "role": role,
            "content": content,
        }
        
        if metadata:
            payload["metadata"] = metadata
        
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
                
                logger.debug(f"Added message to Foundry thread {thread_id}: role={role}, content_length={len(content)}")
                return data
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to add message to Foundry thread: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error adding message to Foundry thread: {e}")
            raise
    
    async def list_messages(
        self,
        thread_id: str,
        limit: int = 20,
    ) -> list[dict]:
        """
        List messages in a thread.
        
        Args:
            thread_id: Thread identifier
            limit: Maximum number of messages to return
            
        Returns:
            List of message dictionaries
        """
        url = f"{self.base_url}/threads/{thread_id}/messages"
        headers = await self._get_headers()
        
        params = {
            "api-version": self.api_version,
            "limit": limit,
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    headers=headers,
                    params=params,
                )
                response.raise_for_status()
                data = response.json()
                
                messages = data.get("data", []) if isinstance(data, dict) else data
                logger.debug(f"Listed {len(messages)} messages from Foundry thread {thread_id}")
                return messages
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to list messages from Foundry thread: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error listing messages from Foundry thread: {e}")
            raise
    
    async def upload_file(
        self,
        thread_id: str,
        file_path: str,
        purpose: str = "assistant",
    ) -> dict:
        """
        Upload a file to a thread (for file-based RAG).
        
        Args:
            thread_id: Thread identifier
            file_path: Path to file to upload
            purpose: File purpose (assistant, user, etc.)
            
        Returns:
            File details (dict)
        """
        url = f"{self.base_url}/threads/{thread_id}/files"
        headers = await self._get_headers()
        
        # Remove Content-Type for multipart upload
        headers.pop("Content-Type", None)
        
        try:
            with open(file_path, "rb") as f:
                files = {"file": (file_path, f, "application/octet-stream")}
                data = {"purpose": purpose}
                
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        url,
                        headers=headers,
                        files=files,
                        data=data,
                        params={"api-version": self.api_version},
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    logger.info(f"Uploaded file to Foundry thread {thread_id}: {file_path}")
                    return data
                    
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to upload file to Foundry thread: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error uploading file to Foundry thread: {e}")
            raise
    
    async def create_agent(
        self,
        name: str,
        instructions: str,
        model: str,
        tools: list[dict],
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        Create an agent in Foundry Agent Service.
        
        Args:
            name: Agent name
            instructions: System prompt/instructions
            model: Model deployment name
            tools: List of tool definitions (function definitions)
            metadata: Optional agent metadata
            
        Returns:
            Agent details (dict with 'id' field)
        """
        url = f"{self.base_url}/agents"
        headers = await self._get_headers()
        
        # Foundry Agent Service requires "name" at root and "definition" with "kind"
        # Kind must be one of: prompt, hosted, container_app, workflow
        # For agents with instructions/model/tools, use "prompt" (hosted requires container config)
        payload = {
            "name": name,
            "definition": {
                "kind": "prompt",  # Use "prompt" for simple agents with instructions/model/tools
                "instructions": instructions,
                "model": model,
                "tools": tools or [],
                "temperature": 0.7,
            }
        }
        
        if metadata:
            payload["definition"]["metadata"] = metadata
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                    params={"api-version": self.api_version},
                )
                response.raise_for_status()
                data = response.json()
                
                logger.info(f"Created Foundry agent: {name} (ID: {data.get('id', 'unknown')})")
                return data
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to create Foundry agent: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error creating Foundry agent: {e}")
            raise
    
    async def get_agent(self, agent_id: str) -> dict:
        """
        Get agent details from Foundry.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Agent details (dict)
        """
        url = f"{self.base_url}/agents/{agent_id}"
        headers = await self._get_headers()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    headers=headers,
                    params={"api-version": self.api_version},
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get Foundry agent: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error getting Foundry agent: {e}")
            raise
    
    async def list_agents(self, limit: int = 20) -> list[dict]:
        """
        List agents in Foundry project.
        
        Args:
            limit: Maximum number of agents to return
            
        Returns:
            List of agent dictionaries
        """
        url = f"{self.base_url}/agents"
        headers = await self._get_headers()
        
        params = {
            "api-version": self.api_version,
            "limit": limit,
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    headers=headers,
                    params=params,
                )
                response.raise_for_status()
                data = response.json()
                
                agents = data.get("data", []) if isinstance(data, dict) else data
                logger.info(f"Listed {len(agents)} Foundry agents")
                return agents
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to list Foundry agents: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error listing Foundry agents: {e}")
            raise
    
    async def delete_thread(self, thread_id: str) -> None:
        """
        Delete a thread.
        
        Args:
            thread_id: Thread identifier
        """
        url = f"{self.base_url}/threads/{thread_id}"
        headers = await self._get_headers()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    url,
                    headers=headers,
                    params={"api-version": self.api_version},
                )
                response.raise_for_status()
                
                logger.info(f"Deleted Foundry thread: {thread_id}")
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to delete Foundry thread: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error deleting Foundry thread: {e}")
            raise


# Singleton instance (lazy-loaded)
_foundry_client: Optional[FoundryAgentServiceClient] = None


def get_foundry_client() -> Optional[FoundryAgentServiceClient]:
    """
    Get or create Foundry Agent Service client singleton.
    
    Returns None if Foundry is not configured (feature flags disabled).
    This ensures zero impact when Foundry is not in use.
    """
    global _foundry_client
    
    settings = get_settings()
    
    # Only create client if Foundry is configured
    # For agent creation, we need the client even if feature flags are disabled
    # So we check if Foundry endpoint and project are configured
    if not settings.azure_foundry_agent_endpoint or not settings.azure_foundry_agent_project:
        return None
    
    if _foundry_client is None:
        try:
            _foundry_client = FoundryAgentServiceClient()
            logger.info("Foundry Agent Service client initialized")
        except (ValueError, Exception) as e:
            logger.warning(f"Foundry Agent Service client initialization failed (non-blocking): {e}")
            return None
    
    return _foundry_client

