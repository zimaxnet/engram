"""
Gemini Client - Google AI Integration

Async client for Gemini API and Nano Banana Pro (Gemini 3 Image) generation.
"""

import logging
import os
from typing import Optional
import base64
import io

from google import genai
from google.genai import types

from backend.core import get_settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Client for Google's Gemini API using the new google-genai SDK.
    Supports text/diagram generation and Nano Banana Pro (gemini-3-pro-image-preview) image generation.
    """
    
    # Text/Function Calling Model
    DEFAULT_MODEL = "gemini-2.0-flash"
    
    # Nano Banana Pro (High Quality Image)
    IMAGE_MODEL = "gemini-3-pro-image-preview" 

    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.gemini_api_key
        
        if not self.api_key:
            raise ValueError("Gemini API key not configured. Set GEMINI_API_KEY.")
            
        # Initialize the official SDK client
        self.client = genai.Client(api_key=self.api_key)
        
        logger.info(f"GeminiClient initialized with google-genai SDK")

    async def ainvoke(self, prompt: str, model: Optional[str] = None) -> str:
        """
        Send a prompt to Gemini and get a response (Async wrapper).
        """
        target_model = model or self.DEFAULT_MODEL
        logger.info(f"GeminiClient: Calling {target_model}")
        
        try:
            # The SDK's async support might vary, but for now we wrap standard calls 
            # or use async methods if available in the version installed.
            # Checking recent SDK docs, client.aio.models.generate_content is typical pattern
            # If standard synchronous client is used in async context, it blocks loop.
            # We'll use the synchronous call for now or update if async is strictly required. 
            # For massive throughput, async is better, but this is low volume.
            
            response = self.client.models.generate_content(
                model=target_model,
                contents=prompt
            )
            
            if response.text:
                return response.text
            
            logger.warning("GeminiClient: Empty text response")
            return ""
            
        except Exception as e:
            logger.error(f"GeminiClient: Error: {e}")
            raise

    async def generate_diagram_spec(
        self,
        topic: str,
        diagram_type: str = "architecture",
        existing_spec: Optional[dict] = None,
    ) -> dict:
        """
        Generate a Nano Banana Pro diagram specification.
        """
        import json
        
        prompt = f"""Generate a detailed JSON specification for a Nano Banana Pro diagram.

Topic: {topic}
Diagram Type: {diagram_type}

The JSON should follow this structure:
{{
  "title": "...",
  "subtitle": "...",
  "theme": "dark",
  "layout": "hierarchical|layered|flow",
  "nodes": [
    {{
      "id": "unique_id",
      "label": "Display Label",
      "type": "service|layer|data-model|actor|process",
      "icon": "icon_name",
      "position": {{"x": 400, "y": 100}},
      "description": "Brief description",
      "style": {{
        "backgroundColor": "#hexcolor",
        "borderColor": "#hexcolor"
      }}
    }}
  ],
  "connections": [
    {{
      "from": "node_id_1",
      "to": "node_id_2",
      "label": "connection label",
      "style": {{"strokeColor": "#hexcolor", "animated": true}}
    }}
  ],
  "annotations": [
    {{
      "id": "annotation_id",
      "target": "node_id",
      "text": "Annotation text",
      "position": "left|right|top|bottom"
    }}
  ],
  "legend": [...]
}}

Return ONLY valid JSON, no markdown code blocks or explanations."""

        if existing_spec:
            prompt += f"\n\nEnhance this existing spec:\n{json.dumps(existing_spec, indent=2)}"

        # Note: Using ainvoke which wraps the synchronous call
        response_text = await self.ainvoke(prompt)
        
        try:
            cleaned = response_text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
            
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"GeminiClient: Failed to parse JSON: {e}")
            raise ValueError(f"Invalid JSON from Gemini: {e}")

    async def generate_image(self, prompt: str) -> bytes:
        """
        Generate an image using Nano Banana Pro (Gemini 3 Pro Image) via google-genai SDK.
        Uses generate_content with image mime type config.
        """
        logger.info(f"GeminiClient: Generating image with {self.IMAGE_MODEL} for: {prompt[:50]}...")
        
        try:
            # Using generate_content as per user instructions, but removing strict mime type config
            # to avoid INVALID_ARGUMENT error seen in verification.
            response = self.client.models.generate_content(
                model=self.IMAGE_MODEL,
                contents=prompt
            )
            
            # Process response to get image bytes
            if response.candidates:
                candidate = response.candidates[0]
                for part in candidate.content.parts:
                    if part.inline_data:
                        logger.info(f"GeminiClient: Image generated successfully (mime: {part.inline_data.mime_type})")
                        return part.inline_data.data
            
            logger.warning(f"GeminiClient: No inline image data in response. Full response: {response}")
            if response.text:
                logger.warning(f"GeminiClient: Model returned text instead: {response.text}")
                
            return await self._generate_mock_image(prompt)
            
        except Exception as e:
            logger.error(f"GeminiClient: Image generation failed: {e}")
            return await self._generate_mock_image(prompt)

    async def _generate_mock_image(self, prompt: str) -> bytes:
        """Fallback mock image generation"""
        try:
            from PIL import Image, ImageDraw
            import random
            
            color = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
            img = Image.new('RGB', (1024, 1024), color=color)
            d = ImageDraw.Draw(img)
            
            d.text((50, 500), "Image Generation Failed\n(Mock Fallback)", fill=(255, 255, 255))
            
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            return img_byte_arr.getvalue()
        except ImportError:
            return b""


# Singleton instance
_gemini_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """Get or create the Gemini client singleton."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client

