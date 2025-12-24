"""
Claude Client - Anthropic API Integration

Async client for Claude models (Opus 4.5) for story generation.
Used by Sage Meridian for creating compelling narratives.
"""

import logging
from typing import Optional

import httpx

from backend.core import get_settings

logger = logging.getLogger(__name__)


class ClaudeClient:
    """
    Async client for Anthropic's Claude API.
    
    Uses Claude Opus for creative story generation with
    high-quality prose and narrative structure.
    """

    ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
    DEFAULT_MODEL = "claude-sonnet-4-20250514"  # Claude Sonnet 4 (latest)

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 8192,
        temperature: float = 0.8,  # Higher for creative writing
        timeout: float = 120.0,
    ):
        settings = get_settings()
        self.api_key = api_key or settings.anthropic_api_key
        if not self.api_key:
            logger.warning("Anthropic API key not configured. ANTHROPIC_API_KEY is missing.")
        
        self.model = model or self.DEFAULT_MODEL
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }
        
        logger.info(f"ClaudeClient initialized: model={self.model}")

    async def ainvoke(
        self,
        messages: list[dict],
        system: Optional[str] = None,
    ) -> str:
        """
        Send messages to Claude and get a response.
        Falls back to APIM gateway (Azure OpenAI) if Anthropic returns 429.
        """
        if not self.api_key:
            logger.warning("ClaudeClient: No API key, falling back to APIM gateway.")
            return await self._fallback_to_apim(messages, system)

        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": messages,
        }
        
        if system:
            payload["system"] = system

        logger.info(f"ClaudeClient: Calling {self.ANTHROPIC_API_URL} with model={self.model}")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    self.ANTHROPIC_API_URL,
                    headers=self.headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract text from Claude's response format
                content = data.get("content", [])
                if content and isinstance(content, list):
                    text_blocks = [block.get("text", "") for block in content if block.get("type") == "text"]
                    result = "\n".join(text_blocks)
                else:
                    result = ""
                
                logger.info(f"ClaudeClient: Response received, length={len(result)}")
                return result
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    logger.warning(f"ClaudeClient: Rate limited (429), falling back to APIM gateway.")
                    return await self._fallback_to_apim(messages, system)
                logger.error(f"ClaudeClient: HTTP error {e.response.status_code}: {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"ClaudeClient: Error calling Claude: {e}")
                raise

    async def _fallback_to_apim(
        self,
        messages: list[dict],
        system: Optional[str] = None,
    ) -> str:
        """
        Fallback to APIM gateway (Azure OpenAI) when Claude is unavailable or rate-limited.
        """
        settings = get_settings()
        
        endpoint = settings.azure_ai_endpoint
        api_key = settings.azure_ai_key
        deployment = settings.azure_ai_deployment or "gpt-4o"
        api_version = settings.azure_ai_api_version or "2024-10-01-preview"
        
        if not endpoint or not api_key:
            raise ValueError("APIM fallback not configured. Set AZURE_AI_ENDPOINT and AZURE_AI_KEY.")
        
        # Build URL - handle trailing slash
        # Note: OpenAI-compatible v1 endpoints don't need api-version
        base = endpoint.rstrip("/")
        url = f"{base}/chat/completions"
        
        # Convert Claude messages to OpenAI format
        openai_messages = []
        if system:
            openai_messages.append({"role": "system", "content": system})
        for msg in messages:
            openai_messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        
        payload = {
            "model": deployment,
            "messages": openai_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        
        headers = {
            "Content-Type": "application/json",
            "api-key": api_key,
        }
        
        logger.info(f"ClaudeClient: Fallback to APIM gateway at {url}")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Extract from OpenAI format
            choices = data.get("choices", [])
            if choices:
                result = choices[0].get("message", {}).get("content", "")
            else:
                result = ""
            
            logger.info(f"ClaudeClient: APIM fallback response received, length={len(result)}")
            return result

    async def generate_story(
        self,
        topic: str,
        context: Optional[str] = None,
        style: str = "technical narrative",
    ) -> str:
        """
        Generate a story about a given topic.
        
        Args:
            topic: The subject of the story
            context: Optional background context
            style: Writing style (default: technical narrative)
            
        Returns:
            Generated story in markdown format
        """
        system_prompt = f"""You are Sage Meridian, a master storyteller who transforms complex technical concepts into compelling narratives. Your writing style is:

- **Eloquent**: Prose that flows naturally and engages the reader
- **Visual**: Uses vivid metaphors from nature and architecture
- **Precise**: Technical accuracy without sacrificing readability
- **Structured**: Clear sections with headers, code blocks, and diagrams

Write in a {style} style. Use markdown formatting with:
- Headers (##, ###)
- Code blocks for technical details
- Tables for comparisons
- Blockquotes for key insights

The output should be a complete, self-contained story document."""

        user_message = f"Create a story about: {topic}"
        if context:
            user_message += f"\n\nContext:\n{context}"

        messages = [{"role": "user", "content": user_message}]
        
        return await self.ainvoke(messages, system=system_prompt)


# Singleton instance
_claude_client: Optional[ClaudeClient] = None


def get_claude_client() -> ClaudeClient:
    """Get or create the Claude client singleton."""
    global _claude_client
    if _claude_client is None:
        _claude_client = ClaudeClient()
    return _claude_client
