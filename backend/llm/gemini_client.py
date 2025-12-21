"""
Gemini Client - Google AI Integration

Async client for Gemini API for diagram generation via Nano Banana Pro.
"""

import logging
from typing import Optional

import httpx

from backend.core import get_settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """
    Async client for Google's Gemini API.
    
    Used for generating diagrams via Nano Banana Pro integration.
    """

    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    DEFAULT_MODEL = "gemini-2.0-flash"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 60.0,
    ):
        settings = get_settings()
        self.api_key = api_key or settings.gemini_api_key
        if not self.api_key:
            raise ValueError("Gemini API key not configured. Set GEMINI_API_KEY.")
        
        self.model = model or self.DEFAULT_MODEL
        self.timeout = timeout
        
        logger.info(f"GeminiClient initialized: model={self.model}")

    async def ainvoke(self, prompt: str) -> str:
        """
        Send a prompt to Gemini and get a response.
        
        Args:
            prompt: The prompt text
            
        Returns:
            Response text from Gemini
        """
        url = f"{self.GEMINI_API_URL}/{self.model}:generateContent?key={self.api_key}"
        
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 8192,
            }
        }

        logger.info(f"GeminiClient: Calling {self.model}")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                
                # Extract text from Gemini's response format
                candidates = data.get("candidates", [])
                if candidates:
                    content = candidates[0].get("content", {})
                    parts = content.get("parts", [])
                    if parts:
                        result = parts[0].get("text", "")
                        logger.info(f"GeminiClient: Response received, length={len(result)}")
                        return result
                
                logger.warning("GeminiClient: Empty response")
                return ""
                
            except httpx.HTTPStatusError as e:
                logger.error(f"GeminiClient: HTTP error {e.response.status_code}: {e.response.text}")
                raise
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
        
        Args:
            topic: Subject of the diagram
            diagram_type: Type of diagram (architecture, flow, layer, etc.)
            existing_spec: Optional existing spec to enhance
            
        Returns:
            JSON specification for Nano Banana Pro
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

        response = await self.ainvoke(prompt)
        
        # Parse JSON from response
        try:
            # Clean up response if it has markdown code blocks
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
            
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"GeminiClient: Failed to parse JSON: {e}")
            logger.error(f"Response was: {response[:500]}")
            raise ValueError(f"Invalid JSON from Gemini: {e}")


# Singleton instance
_gemini_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """Get or create the Gemini client singleton."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client
