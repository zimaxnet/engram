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
    settings = get_settings()
    docs_path = Path(settings.onedrive_docs_path or "docs")
    stories_dir = docs_path / "stories"
    images_dir = docs_path / "images"
    
    if not stories_dir.exists():
        logger.error(f"Stories directory not found: {stories_dir}")
        return

    images_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Get all stories from disk
    story_files = list(stories_dir.glob("*.md"))
    logger.info(f"Found {len(story_files)} stories in {stories_dir}")
    
    # 2. Get all sessions from Zep to find user_ids
    # Note: We need user_id to update metadata in Zep
    all_sessions = await memory_client.list_sessions(limit=100)
    session_map = {s["session_id"]: s for s in all_sessions}
    logger.info(f"Fetched {len(all_sessions)} sessions from Zep")
    
    gemini = get_gemini_client()
    
    # Track results
    repaired = 0
    skipped = 0
    errors = 0

    for story_file in story_files:
        story_id = story_file.stem
        image_file = images_dir / f"{story_id}.png"
        image_web_path = f"/api/v1/images/{story_id}.png"
        
        logger.info(f"Checking story: {story_id}")
        
        # A. Handle disk image
        if not image_file.exists():
            logger.info(f"  [X] Image missing on disk: {image_file}. Regenerating...")
            
            # Read story content for context
            try:
                content = story_file.read_text(encoding="utf-8")
                topic = story_id.split("-", 2)[-1].replace("-", " ") if "-" in story_id else story_id
                
                # Step 1: Generate visual spec
                logger.info(f"    - Generating visual spec for: {topic}")
                visual_spec = await gemini.generate_visual_spec(
                    topic=topic,
                    context=f"Story illustration for metadata repair. Content preview: {content[:500]}"
                )
                
                # Step 2: Generate image from spec
                logger.info(f"    - Generating image from spec using Nano Banana Pro...")
                image_data = await gemini.generate_image_from_spec(visual_spec)
                
                if image_data:
                    image_file.write_bytes(image_data)
                    logger.info(f"    - Saved regenerated image: {image_file}")
                else:
                    logger.error(f"    - Failed to generate image data for {story_id}")
                    errors += 1
                    continue
            except Exception as e:
                logger.error(f"    - Error regenerating image: {e}")
                errors += 1
                continue
        else:
            logger.info(f"  [OK] Image exists on disk")

        # B. Handle Zep Memory Metadata
        session_id = f"story-{story_id}"
        zep_session = session_map.get(session_id)
        
        if zep_session:
            user_id = zep_session.get("user_id")
            current_metadata = zep_session.get("metadata", {}) or {}
            
            if current_metadata.get("image_path") != image_web_path:
                logger.info(f"  [X] Zep metadata mismatch. Updating {session_id}...")
                new_metadata = {**current_metadata, "image_path": image_web_path}
                
                try:
                    await memory_client.get_or_create_session(
                        session_id=session_id,
                        user_id=user_id,
                        metadata=new_metadata
                    )
                    logger.info(f"    - Zep metadata updated successfully")
                    repaired += 1
                except Exception as e:
                    logger.error(f"    - Failed to update Zep metadata: {e}")
                    errors += 1
            else:
                logger.info(f"  [OK] Zep metadata is correct")
                skipped += 1
        else:
            logger.warning(f"  [?] Session {session_id} not found in Zep. Skipping metadata update.")
            skipped += 1

    # C. Handle orphan Zep stories (in Zep but not on disk)
    for session_id, sess in session_map.items():
        if not session_id.startswith("story-"):
            continue
            
        story_id = sess.get("metadata", {}).get("story_id")
        if not story_id:
            # Try to extract from session_id
            story_id = session_id.replace("story-", "")
            
        story_file = stories_dir / f"{story_id}.md"
        if not story_file.exists():
            logger.warning(f"  [!] Story {story_id} exists in Zep but is missing on disk: {story_file}")

    logger.info("-" * 40)
    logger.info(f"Repair process completed:")
    logger.info(f"  Repaired/Updated: {repaired}")
    logger.info(f"  Already correct:  {skipped}")
    logger.info(f"  Errors encountered: {errors}")

if __name__ == "__main__":
    asyncio.run(repair_stories())
