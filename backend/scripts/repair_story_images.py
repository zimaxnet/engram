#!/usr/bin/env python3
"""
Repair Story Images Script

Audits existing stories in docs/stories and ensures they have:
1. A corresponding image in docs/images
2. Correct image_path metadata in Zep memory

If an image is missing, it triggers Sage's image generation pipeline.
"""

import asyncio
import logging
import os
from pathlib import Path
from datetime import datetime
import json
import httpx

from backend.core import get_settings
from backend.memory.client import memory_client, ZepMemoryClient
from backend.llm.gemini_client import get_gemini_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("repair_story_images")


async def repair_stories():
    """
    Repair stories by triggering the API to generate missing visuals.
    """
    api_base = os.getenv("ENGRAM_API_URL", "https://engram.work")
    api_token = os.getenv("ENGRAM_API_TOKEN")
    
    if not api_token:
        print("Error: ENGRAM_API_TOKEN is required")
        return

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(base_url=api_base, headers=headers, timeout=60.0) as client:
        # 1. List all stories
        print(f"Fetching stories from {api_base}...")
        try:
            resp = await client.get("/api/v1/story/")
            resp.raise_for_status()
            stories = resp.json()
        except Exception as e:
            print(f"Failed to list stories: {e}")
            return

        print(f"Found {len(stories)} stories.")
        
        repaired = 0
        skipped = 0
        errors = 0

        for story in stories:
            story_id = story["story_id"]
            topic = story["topic"]
            image_path = story.get("image_path")
            
            print(f"Checking story [{story_id}]: {topic[:30]}...")
            
            if image_path:
                print(f"  [OK] Image exists: {image_path}")
                skipped += 1
                continue
                
            print(f"  [X] Image MISSING. Triggering generation...")
            
            try:
                # Trigger visual generation
                # We use the topic as the prompt
                gen_resp = await client.post(
                    f"/api/v1/story/{story_id}/visual",
                    json={"prompt": topic}
                )
                gen_resp.raise_for_status()
                print(f"    - SUCCESS: Visual generated.")
                repaired += 1
            except Exception as e:
                print(f"    - FAILED: {e}")
                errors += 1
                
        print("-" * 40)
        print(f"Repair complete: Repaired {repaired}, Skipped {skipped}, Errors {errors}")

if __name__ == "__main__":
    asyncio.run(repair_stories())
