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

    async def generate_visual_spec(self, topic: str, context: str = "") -> dict:
        """
        Generate a visual specification (JSON) describing the image to create.
        This is step 1 of the two-step flow: spec → image.
        
        Returns a dict with: style, subject, mood, colors, composition
        """
        import json
        
        prompt = f"""Generate a JSON specification for an AI-generated visual.

Topic: {topic}
Context: {context}

Return ONLY valid JSON with this structure:
{{
  "title": "Brief title for the image",
  "style": "digital art|photorealistic|illustration|abstract|concept art",
  "subject": "Main subject/scene description",
  "mood": "emotional tone (triumphant, serene, dramatic, etc.)",
  "colors": ["primary color", "secondary color", "accent color"],
  "composition": "Layout description (centered, rule of thirds, etc.)",
  "elements": ["key element 1", "key element 2", "key element 3"],
  "prompt": "Optimized prompt for image generation combining all above"
}}

No markdown code blocks, just JSON."""

        response_text = await self.ainvoke(prompt)
        
        try:
            cleaned = response_text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"GeminiClient: Failed to parse visual spec JSON: {e}")
            # Return a basic spec as fallback
            return {
                "title": topic,
                "style": "digital art",
                "subject": topic,
                "mood": "professional",
                "colors": ["#00d4ff", "#1a1a2e", "#4a4a6a"],
                "composition": "centered",
                "elements": [topic],
                "prompt": f"Professional digital art depicting {topic}, high quality, detailed"
            }

    async def generate_image_from_spec(self, spec: dict) -> bytes:
        """
        Generate an image from a visual specification.
        This is step 2 of the two-step flow: spec → image.
        
        Uses Nano Banana Pro (Gemini 3 Pro Image) with proper response_modalities config.
        """
        prompt = spec.get("prompt", f"Create {spec.get('subject', 'an image')}")
        logger.info(f"GeminiClient: Generating image from spec: {spec.get('title', 'untitled')}")
        
        return await self.generate_image(prompt)

    async def generate_image(self, prompt: str) -> bytes:
        """
        Generate an image using Nano Banana Pro (Gemini 3 Pro Image) via google-genai SDK.
        Uses generate_content with response_modalities config for image output.
        """
        logger.info(f"GeminiClient: Generating image with {self.IMAGE_MODEL} for: {prompt[:50]}...")
        
        try:
            # Configure for image generation with response_modalities
            # This tells the model we want image output, not just text
            response = self.client.models.generate_content(
                model=self.IMAGE_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                )
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
                logger.warning(f"GeminiClient: Model returned text instead: {response.text[:200]}")
                
            return await self._generate_mock_image(prompt)
            
        except Exception as e:
            logger.error(f"GeminiClient: Image generation failed: {e}")
            return await self._generate_mock_image(prompt)

    async def _generate_mock_image(self, prompt: str) -> bytes:
        """Fallback mock image generation with better styling"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import random
            
            # Create a nicer looking fallback image
            width, height = 1024, 1024
            
            # Dark gradient background
            img = Image.new('RGB', (width, height), color=(26, 26, 46))
            d = ImageDraw.Draw(img)
            
            # Add some visual interest
            for i in range(20):
                x = random.randint(0, width)
                y = random.randint(0, height)
                r = random.randint(50, 150)
                alpha = random.randint(10, 30)
                d.ellipse([x-r, y-r, x+r, y+r], fill=(0, 212, 255, alpha))
            
            # Center text
            text = "Visual Generation\nPending"
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
            except:
                font = ImageFont.load_default()
            
            # Get text bounding box for centering
            bbox = d.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            d.text((x, y), text, fill=(255, 255, 255), font=font, align="center")
            
            # Add prompt snippet at bottom
            snippet = prompt[:80] + "..." if len(prompt) > 80 else prompt
            d.text((50, height - 100), f"Prompt: {snippet}", fill=(150, 150, 150))
            
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

