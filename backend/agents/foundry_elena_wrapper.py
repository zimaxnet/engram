"""
Foundry Elena Agent Wrapper

Wraps Azure AI Foundry agent for Elena, providing Engram-compatible interface.
Maintains Microsoft Graph integration and all Elena's capabilities.
"""

import logging
from typing import Optional
import httpx
from datetime import datetime, timezone

from backend.agents.foundry_client import get_foundry_client
from backend.core import EnterpriseContext, MessageRole, Turn, get_settings

logger = logging.getLogger(__name__)


class FoundryElenaWrapper:
    """
    Wrapper for Foundry-created Elena agent.
    
    Provides Engram-compatible interface while using Foundry's agent runtime.
    Maintains all Elena's capabilities including Microsoft Graph integration.
    """
    
    def __init__(self, foundry_agent_id: str):
        """
        Initialize Foundry Elena wrapper.
        
        Args:
            foundry_agent_id: Foundry agent ID for Elena
        """
        self.agent_id = "elena"
        self.agent_name = "Dr. Elena Vasquez"
        self.agent_title = "Business Analyst"
        self.foundry_agent_id = foundry_agent_id
        self.foundry_client = get_foundry_client()
        
        if not self.foundry_client:
            raise ValueError("Foundry client not available. Check configuration.")
        
        logger.info(f"FoundryElenaWrapper initialized: foundry_agent_id={foundry_agent_id}")
    
    async def run(
        self,
        user_message: str,
        context: EnterpriseContext,
        thread_id: Optional[str] = None
    ) -> tuple[str, EnterpriseContext, Optional[str]]:
        """
        Execute Foundry Elena agent with user message.
        
        Args:
            user_message: User's input message
            context: Enterprise context
            thread_id: Optional Foundry thread ID (creates new if not provided)
            
        Returns:
            Tuple of (response_text, updated_context, avatar_video_url)
        """
        # Get or create Foundry thread
        if not thread_id:
            thread_id = await self.foundry_client.create_thread(
                user_id=context.security.user_id,
                agent_id=self.agent_id,
                project_id=context.security.project_id,
                metadata={
                    "session_id": context.episodic.conversation_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            logger.info(f"Created Foundry thread {thread_id} for Elena")
        
        # Add user message to thread
        await self.foundry_client.add_message(
            thread_id=thread_id,
            role="user",
            content=user_message,
            metadata={
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
        
        # Add user turn to context
        user_turn = Turn(
            role=MessageRole.USER,
            content=user_message,
            timestamp=datetime.now(timezone.utc),
        )
        context.episodic.add_turn(user_turn)
        
        # Run Foundry agent
        response_text = await self._run_foundry_agent(thread_id)
        
        # Add assistant response to thread
        await self.foundry_client.add_message(
            thread_id=thread_id,
            role="assistant",
            content=response_text,
            metadata={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent_id": self.agent_id,
            },
        )
        
        # Add assistant turn to context
        assistant_turn = Turn(
            role=MessageRole.ASSISTANT,
            content=response_text,
            timestamp=datetime.now(timezone.utc),
            agent_id=self.agent_id,
        )
        context.episodic.add_turn(assistant_turn)
        
        # Update context metadata
        context.episodic.conversation_id = thread_id
        if not context.episodic.metadata:
            context.episodic.metadata = {}
        context.episodic.metadata.update({
            "foundry_thread_id": thread_id,
            "foundry_agent_id": self.foundry_agent_id,
        })
        context.update_timestamp()
        
        return response_text, context, avatar_video_url
    
    async def _run_foundry_agent_with_avatar(self, thread_id: str) -> tuple[str, Optional[str]]:
        """
        Execute Foundry agent with avatar enabled using responses API.
        
        This uses Foundry's responses API which supports avatar video generation.
        
        Returns:
            Tuple of (response_text, avatar_video_url)
        """
        # Use Foundry's responses API with avatar enabled
        # Format: /api/projects/{project}/applications/{agent}/protocols/openai/responses
        # base_url is: https://zimax.services.ai.azure.com/api/projects/zimax
        # We need: https://zimax.services.ai.azure.com/api/projects/zimax/applications/{agent}/protocols/openai/responses
        base_endpoint = self.foundry_client.endpoint.rstrip("/")
        url = f"{base_endpoint}/api/projects/{self.foundry_client.project}/applications/{self.foundry_agent_id}/protocols/openai/responses"
        headers = await self.foundry_client._get_headers()
        
        # Get thread messages for context
        messages = await self.foundry_client.list_messages(thread_id, limit=10)
        message_history = [
            {"role": msg.get("role", "user"), "content": msg.get("content", "")}
            for msg in reversed(messages)  # Reverse to get chronological order
        ]
        
        # Add user message if not already in history
        if not message_history or message_history[-1].get("role") != "user":
            message_history.append({"role": "user", "content": messages[-1].get("content", "") if messages else ""})
        
        payload = {
            "input": message_history,
            "extra_body": {
                "agent": {
                    "name": self.foundry_agent_id,
                    "type": "agent_reference"
                },
                "avatar": {
                    "enabled": True,
                    "resolution": "1080p",
                    "emotion": "neutral"
                }
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                    params={"api-version": self.foundry_client.api_version},
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract response text and avatar video URL
                response_text = data.get("output_text", "") or data.get("content", "")
                avatar_video_url = data.get("avatar_video_url") or data.get("avatar", {}).get("video_url")
                
                logger.info(f"Foundry agent response received: text_length={len(response_text)}, avatar_video={bool(avatar_video_url)}")
                
                return response_text, avatar_video_url
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to run Foundry agent with avatar: {e.response.status_code} - {e.response.text}")
            # Fallback to regular run without avatar
            logger.warning("Falling back to regular agent run without avatar")
            response_text = await self._run_foundry_agent(thread_id)
            return response_text, None
        except Exception as e:
            logger.error(f"Error running Foundry agent with avatar: {e}", exc_info=True)
            # Fallback to regular run without avatar
            logger.warning("Falling back to regular agent run without avatar")
            try:
                response_text = await self._run_foundry_agent(thread_id)
                return response_text, None
            except:
                raise
    
    async def _run_foundry_agent(self, thread_id: str) -> str:
        """
        Execute Foundry agent on thread and wait for response (fallback method).
        
        This uses Foundry's agent execution API to run the agent without avatar.
        """
        url = f"{self.foundry_client.base_url}/threads/{thread_id}/runs"
        headers = await self.foundry_client._get_headers()
        
        payload = {
            "assistant_id": self.foundry_agent_id,
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                # Create run
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                    params={"api-version": self.foundry_client.api_version},
                )
                response.raise_for_status()
                run_data = response.json()
                run_id = run_data.get("id")
                
                if not run_id:
                    raise ValueError(f"Run creation response missing 'id': {run_data}")
                
                logger.info(f"Created Foundry agent run {run_id} for thread {thread_id}")
                
                # Wait for run to complete
                return await self._wait_for_run_completion(thread_id, run_id)
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to run Foundry agent: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error running Foundry agent: {e}", exc_info=True)
            raise
    
    async def _wait_for_run_completion(self, thread_id: str, run_id: str, max_wait: int = 120) -> str:
        """
        Wait for agent run to complete and retrieve response.
        
        Args:
            thread_id: Foundry thread ID
            run_id: Foundry run ID
            max_wait: Maximum seconds to wait
            
        Returns:
            Agent response text
        """
        import asyncio
        
        url = f"{self.foundry_client.base_url}/threads/{thread_id}/runs/{run_id}"
        headers = await self.foundry_client._get_headers()
        
        start_time = asyncio.get_event_loop().time()
        
        while True:
            # Check elapsed time
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > max_wait:
                raise TimeoutError(f"Agent run {run_id} did not complete within {max_wait} seconds")
            
            # Poll run status
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    headers=headers,
                    params={"api-version": self.foundry_client.api_version},
                )
                response.raise_for_status()
                run_data = response.json()
                
                status = run_data.get("status", "unknown")
                
                if status == "completed":
                    # Get latest assistant message from thread
                    messages = await self.foundry_client.list_messages(thread_id, limit=1)
                    if messages:
                        latest = messages[0]
                        if latest.get("role") == "assistant":
                            return latest.get("content", "")
                    
                    # Fallback: check run response
                    return run_data.get("response", {}).get("content", "Agent response not available")
                
                elif status == "failed":
                    error = run_data.get("error", {})
                    error_msg = error.get("message", "Unknown error")
                    raise RuntimeError(f"Agent run failed: {error_msg}")
                
                elif status in ["queued", "in_progress"]:
                    # Wait and retry
                    await asyncio.sleep(2)
                    continue
                
                else:
                    logger.warning(f"Unknown run status: {status}")
                    await asyncio.sleep(2)
                    continue

