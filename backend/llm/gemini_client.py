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
    
    # Imagen 3.0 Pro - Highest quality image generation
    # Models: imagen-3.0-generate-002 (stable/quality), imagen-3.0-fast-generate-001 (speed)
    IMAGE_MODEL = "imagen-3.0-generate-002"

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
        story_context: Optional[str] = None,
        existing_spec: Optional[dict] = None,
    ) -> dict:
        """
        Generate a Nano Banana Pro diagram specification.
        """
        import json
        
        context_block = ""
        if story_context:
            context_block = f"""
STORY CONTEXT:
The diagram must align with this narrative description:
"{story_context[:2000]}..."
Ensure node names and relationships reflect the terminology used in the story.
"""

        prompt = f"""Generate a detailed JSON specification for a Nano Banana Pro diagram.

Topic: {topic}
Diagram Type: {diagram_type}
{context_block}

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

    async def generate_visual_spec(self, topic: str, context: str = "", diagram_spec: Optional[dict] = None) -> dict:
        """
        Generate a visual specification (JSON) describing the image to create.
        This is step 1 of the two-step flow: spec → image.
        
        Returns a dict with: style, subject, mood, colors, composition
        """
        import json
        
        # Enhance context with diagram details if available
        diagram_context = ""
        if diagram_spec:
            theme = diagram_spec.get("theme", "modern")
            # Extract up to 5 key node labels to ground the visual
            nodes = diagram_spec.get("nodes", [])
            node_labels = [n.get("label", "") for n in nodes[:5] if n.get("label")]
            node_str = ", ".join(node_labels)
            
            diagram_context = f"""
            ARCHITECTURAL ALIGNMENT REQUIRED:
            This visual MUST align with the provided architectural diagram.
            - Visual Theme: {theme} style
            - Key Components to Visualize: {node_str}
            - Structure: Reflect the interconnected nature of these components.
            """

        prompt = f"""Generate a JSON specification for an AI-generated visual.

Topic: {topic}
Context: {context}
{diagram_context}

Return ONLY valid JSON with this structure:
{{
  "title": "Brief title for the image",
  "style": "digital art|photorealistic|illustration|abstract|concept art",
  "subject": "Main subject/scene description",
  "mood": "emotional tone (triumphant, serene, dramatic, etc.)",
  "colors": ["primary color", "secondary color", "accent color"],
  "composition": "Layout description (centered, rule of thirds, etc.)",
  "elements": ["key element 1", "key element 2", "key element 3"],
  "prompt": "Optimized prompt for image generation combining all above. If architectural components are listed, they MUST be seamlessly integrated into the scene."
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
        Generate an image using Imagen 3.0 Pro via google-genai SDK.
        Uses the dedicated images.generate method for high-quality output.
        safely handles all exceptions to prevent workflow crashes.
        """
        logger.info(f"GeminiClient: Generating image with {self.IMAGE_MODEL} for: {prompt[:50]}...")
        
        try:
            try:
                # Imagen 3.0 uses the images.generate method, not generate_content
                response = self.client.models.generate_images(
                    model=self.IMAGE_MODEL,
                    prompt=prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        aspect_ratio="1:1",  # Square for story cards
                        safety_filter_level="BLOCK_MEDIUM_AND_ABOVE",
                        person_generation="ALLOW_ADULT",
                    )
                )
                
                # Process response to get image bytes
                if response.generated_images:
                    image = response.generated_images[0]
                    if hasattr(image, 'image') and image.image:
                        # The image data is base64 encoded
                        if hasattr(image.image, 'image_bytes'):
                            logger.info(f"GeminiClient: Imagen 3.0 image generated successfully")
                            return image.image.image_bytes
                        elif hasattr(image.image, 'data'):
                            logger.info(f"GeminiClient: Imagen 3.0 image generated successfully (data attr)")
                            return image.image.data
                
                logger.warning(f"GeminiClient: No image data in Imagen response. Response: {response}")
                
            except Exception as e:
                logger.error(f"GeminiClient: Imagen 3.0 generation failed: {e}")
                
                # Try fallback to Gemini multimodal if Imagen isn't available
                try:
                    logger.info("GeminiClient: Falling back to gemini-2.0-flash-exp multimodal...")
                    response = self.client.models.generate_content(
                        model="gemini-2.0-flash-exp",
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_modalities=["IMAGE", "TEXT"],
                        )
                    )
                    
                    if response.candidates:
                        for part in response.candidates[0].content.parts:
                            if part.inline_data:
                                logger.info(f"GeminiClient: Fallback image generated successfully")
                                return part.inline_data.data
                                
                except Exception as fallback_err:
                    logger.error(f"GeminiClient: Fallback also failed: {fallback_err}")
            
            return await self._generate_mock_image(prompt)
            
        except Exception as e:
            logger.error(f"GeminiClient: Critical error in generate_image: {e}")
            return b""

    async def _generate_mock_image(self, prompt: str) -> bytes:
        """Fallback mock image generation with better styling"""
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            logger.warning("GeminiClient: Pillow not installed, cannot generate mock image")
            return b""

        try:
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
                # Try system font, fallback to default
                font_path = "/System/Library/Fonts/Helvetica.ttc"
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, 48)
                else:
                    font = ImageFont.load_default()
            except Exception:
                font = ImageFont.load_default()
            
            # Get text bounding box for centering
            try:
                bbox = d.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                x = (width - text_width) // 2
                y = (height - text_height) // 2
                
                d.text((x, y), text, fill=(255, 255, 255), font=font, align="center")
                
                # Add prompt snippet at bottom
                snippet = prompt[:80] + "..." if len(prompt) > 80 else prompt
                d.text((50, height - 100), f"Prompt: {snippet}", fill=(150, 150, 150))
            except Exception as e:
                logger.warning(f"GeminiClient: Text rendering failed in mock image: {e}")

            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            return img_byte_arr.getvalue()
            
        except Exception as e:
            logger.error(f"GeminiClient: Mock image generation failed: {e}")
            return b""


# Singleton instance
_gemini_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """Get or create the Gemini client singleton."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client

