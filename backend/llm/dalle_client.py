"""
Azure DALL-E 3 Client

Async client for generating images via Azure OpenAI (DALL-E 3).
"""

import logging
import httpx
from typing import Optional
import base64

from backend.core import get_settings

logger = logging.getLogger(__name__)


class DalleClient:
    """
    Client for Azure OpenAI DALL-E 3 image generation.
    """

    def __init__(self, timeout: float = 60.0):
        self.settings = get_settings()
        self.timeout = timeout
        
        self.endpoint = self.settings.azure_ai_endpoint
        self.api_key = self.settings.azure_ai_key
        # Use a specific deployment for DALL-E 3 if configured, else assume "dall-e-3"
        import os
        self.deployment = os.environ.get("AZURE_AI_DALLE_DEPLOYMENT", "dall-e-3")
        self.api_version = "2024-02-01"

    async def generate_image(self, prompt: str, size: str = "1024x1024", quality: str = "standard") -> bytes:
        """
        Generate an image using DALL-E 3.
        
        Args:
            prompt: Image description
            size: Image size (1024x1024, 1024x1792, etc.)
            quality: standard or hd
            
        Returns:
            Image bytes (PNG)
        """
        if not self.endpoint or not self.api_key:
            logger.error("Azure AI credentials not configured for DALL-E.")
            raise ValueError("Azure AI credentials not configured")

        # Construct URL
        # Format: https://{base}/openai/deployments/{deployment}/images/generations?api-version={version}
        base = self.endpoint.rstrip("/").replace("/openai/v1", "")
        url = f"{base}/openai/deployments/{self.deployment}/images/generations?api-version={self.api_version}"
        
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key,
        }
        
        payload = {
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "n": 1,
            "style": "vivid", # or natural
            "response_format": "b64_json" 
        }
        
        logger.info(f"DalleClient: Generating image for '{prompt[:30]}...' via {url}")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                
                # Extract image
                # Response: { created: ..., data: [ { b64_json: ... } ] }
                if "data" in data and len(data["data"]) > 0:
                    b64_json = data["data"][0].get("b64_json")
                    if b64_json:
                        logger.info("DalleClient: Image generated successfully")
                        return base64.b64decode(b64_json)
                
                logger.error(f"DalleClient: No image data in response: {data}")
                return b""
                
            except httpx.HTTPStatusError as e:
                logger.error(f"DalleClient: HTTP error {e.response.status_code}: {e.response.text}")
                # Fallback to mock if it's a 404 (deployment not found) so we don't break the whole workflow in dev
                if e.response.status_code == 404:
                    logger.warning("DalleClient: Deployment not found, falling back to mock.")
                    return await self._generate_mock_image(prompt)
                raise
            except Exception as e:
                logger.error(f"DalleClient: Error generating image: {e}")
                raise

    async def _generate_mock_image(self, prompt: str) -> bytes:
        """Fallback mock image generation"""
        try:
            from PIL import Image, ImageDraw
            import io
            import random
            
            color = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
            img = Image.new('RGB', (1024, 1024), color=color)
            d = ImageDraw.Draw(img)
            d.text((100, 500), f"DALL-E 3 Fallback\n{prompt[:30]}...", fill=(255, 255, 255))
            
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            return img_byte_arr.getvalue()
        except ImportError:
            return b""


# Singleton
_dalle_client: Optional[DalleClient] = None

def get_dalle_client() -> DalleClient:
    global _dalle_client
    if _dalle_client is None:
        _dalle_client = DalleClient()
    return _dalle_client
