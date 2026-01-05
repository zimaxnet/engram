import asyncio
import logging
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load keys from local .env (for LLM) and .env.azure (for Zep)
load_dotenv(".env")
load_dotenv(".env.azure")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("simulate_sage")

# Mock Activity Context for logging
from temporalio import activity
class MockActivityContext:
    def info(self, msg, *args, **kwargs):
        logger.info(msg)
    def error(self, msg, *args, **kwargs):
        logger.error(msg)
    def warning(self, msg, *args, **kwargs):
        logger.warning(msg)

activity.logger = MockActivityContext()

from backend.workflows.story_activities import (
    GenerateStoryInput,
    GenerateImageInput,
    SaveArtifactsInput,
    EnrichMemoryInput,
    generate_story_activity,
    generate_image_activity,
    save_artifacts_activity,
    enrich_story_memory_activity,
)

async def simulate_sage_flow(topic: str):
    logger.info(f"🚀 Starting Sage Simulation: '{topic}'")
    
    # 1. Generate Story (Claude)
    logger.info("--- Step 1: Generating Story ---")
    story_res = await generate_story_activity(GenerateStoryInput(topic=topic))
    
    if not story_res.success:
        logger.error(f"Story generation failed: {story_res.error}")
        return
        
    logger.info(f"✅ Story Generated ({len(story_res.content)} chars)")
    print(f"\n[Story Preview]\n{story_res.content[:500]}...\n")
    
    # 2. Generate Image (Gemini)
    logger.info("--- Step 2: Generating Visual ---")
    # Use the topic as the prompt for simplicity in simulation
    image_res = await generate_image_activity(GenerateImageInput(prompt=topic))
    
    if not image_res.success:
        logger.warning(f"Image generation failed: {image_res.error}")
        image_data = None
    else:
        image_data = image_res.image_data
        logger.info(f"✅ Image Generated ({len(image_data)} bytes)")
        
    # 3. Save Artifacts (OneDrive/Docs)
    logger.info("--- Step 3: Saving Artifacts ---")
    save_res = await save_artifacts_activity(SaveArtifactsInput(
        story_id=story_res.story_id,
        topic=topic,
        story_content=story_res.content,
        image_data=image_data,
        diagram_spec=None # Skipping diagram for this specific request
    ))
    
    if save_res.success:
        logger.info(f"✅ Artifacts Saved: {save_res.story_path}")
        if save_res.image_path:
             logger.info(f"✅ Image Saved: {save_res.image_path}")
    else:
         logger.error(f"Failed to save artifacts: {save_res.error}")

    # 4. Enrich Memory (Zep)
    logger.info("--- Step 4: Enriching Memory ---")
    # For simulation, we use a test user ID or 'sage'
    # 'sage' user might not exist in Zep yet if not bootstrapped
    # We'll use 'sage' and see (Zep might auto-create or fail)
    memory_res = await enrich_story_memory_activity(EnrichMemoryInput(
        user_id="sage", 
        story_id=story_res.story_id,
        topic=topic,
        content=story_res.content,
        image_path=f"/api/v1/images/{story_res.story_id}.png" if image_data else None
    ))
    
    if memory_res.success:
         logger.info(f"✅ Memory Enriched: {memory_res.session_id}")
    else:
         logger.warning(f"Memory enrichment failed: {memory_res.error}")
         
    print(f"\n🏁 Simulation Complete for '{topic}'")
    print(f"Story ID: {story_res.story_id}")

if __name__ == "__main__":
    topic = "The Journey of a Data Packet through Engram"
    if len(sys.argv) > 1:
        topic = sys.argv[1]
    
    asyncio.run(simulate_sage_flow(topic))
