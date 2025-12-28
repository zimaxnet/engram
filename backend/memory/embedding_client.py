"""
Embedding Client for Azure OpenAI.

Generates text embeddings using Azure OpenAI's text-embedding-ada-002 or text-embedding-3-small.
Used for semantic search in search_memory.
"""

import logging
from typing import Optional
import httpx

from backend.core import get_settings

logger = logging.getLogger(__name__)

# Embedding dimensions by model
EMBEDDING_DIMENSIONS = {
    "text-embedding-ada-002": 1536,
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
}

DEFAULT_MODEL = "text-embedding-3-small"  # Available on zimax-gw (ada-002 not deployed)


class EmbeddingClient:
    """Client for generating embeddings via Azure OpenAI."""
    
    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        api_version: str = "2024-02-01",
    ):
        settings = get_settings()
        self.endpoint = endpoint or settings.azure_ai_endpoint
        self.api_key = api_key or settings.azure_ai_key
        self.model = model
        self.api_version = api_version
        self.dimensions = EMBEDDING_DIMENSIONS.get(model, 1536)
        
        if not self.endpoint:
            raise ValueError("Azure AI endpoint not configured. Set AZURE_AI_ENDPOINT.")
        if not self.api_key:
            raise ValueError("Azure AI key not configured. Set AZURE_AI_KEY.")
    
    def _build_url(self) -> str:
        """Build the embeddings API URL."""
        base = self.endpoint.rstrip("/")
        # Handle APIM gateway format
        if "/openai/v1" in base or base.endswith("/v1"):
            return f"{base}/embeddings"
        # Azure AI Foundry / Azure OpenAI format
        return f"{base}/openai/deployments/{self.model}/embeddings?api-version={self.api_version}"
    
    async def generate_embedding(self, text: str) -> list[float]:
        """
        Generate an embedding vector for the given text.
        
        Args:
            text: The text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        url = self._build_url()
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key,
            "Ocp-Apim-Subscription-Key": self.api_key,
        }
        payload = {
            "input": text[:8000],  # Max 8k tokens for ada-002
            "model": self.model,
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                
                embedding = data["data"][0]["embedding"]
                logger.debug(f"Generated embedding with {len(embedding)} dimensions")
                return embedding
                
            except Exception as e:
                logger.error(f"Embedding generation failed: {e}")
                raise
    
    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        url = self._build_url()
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key,
            "Ocp-Apim-Subscription-Key": self.api_key,
        }
        # Truncate each text to 8k chars
        truncated = [t[:8000] for t in texts]
        payload = {
            "input": truncated,
            "model": self.model,
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                
                # Sort by index to maintain order
                sorted_results = sorted(data["data"], key=lambda x: x["index"])
                embeddings = [r["embedding"] for r in sorted_results]
                
                logger.debug(f"Generated {len(embeddings)} embeddings")
                return embeddings
                
            except Exception as e:
                logger.error(f"Batch embedding generation failed: {e}")
                raise


# Singleton instance
_embedding_client: Optional[EmbeddingClient] = None


def get_embedding_client() -> EmbeddingClient:
    """Get or create the embedding client singleton."""
    global _embedding_client
    if _embedding_client is None:
        _embedding_client = EmbeddingClient()
    return _embedding_client


async def generate_embedding(text: str) -> list[float]:
    """Convenience function to generate a single embedding."""
    client = get_embedding_client()
    return await client.generate_embedding(text)
