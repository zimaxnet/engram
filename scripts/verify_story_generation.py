import asyncio
import logging
from backend.core import get_settings
from backend.workflows.client import execute_story

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting Story Generation Verification...")
    
    # Test data
    user_id = "test-user-123"
    tenant_id = "test-tenant-456"
    topic = "The Future of AI Agents in Enterprise"
    
    try:
        # execute_story triggers the Temporal workflow
        logger.info(f"Triggering workflow for topic: {topic}")
        result = await execute_story(
            user_id=user_id,
            tenant_id=tenant_id,
            topic=topic,
            include_diagram=False, # Skip diagram to focus on image
            include_image=True,
            timeout_seconds=600 # 10 minutes
        )
        
        if result.success:
            logger.info("✅ Workflow executed successfully!")
            logger.info(f"Story ID: {result.story_id}")
            logger.info(f"Story Path: {result.story_path}")
            logger.info(f"Image Path: {result.image_path}")
            
            # Verify files exist
            import os
            if result.story_path and os.path.exists(result.story_path):
                logger.info("✅ Story file exists")
            else:
                logger.error("❌ Story file missing")
                
            # Check for image file (path returned is URL-like /api/v1/images/...)
            # We need to check physical path
            settings = get_settings()
            from pathlib import Path
            docs_path = Path(settings.onedrive_docs_path or "docs")
            image_filename = result.image_path.split("/")[-1]
            physical_image_path = docs_path / "images" / image_filename
            
            if physical_image_path.exists():
                logger.info(f"✅ Image file exists at {physical_image_path}")
                logger.info(f"Image size: {physical_image_path.stat().st_size} bytes")
                if physical_image_path.stat().st_size < 1000:
                    logger.warning("⚠️ Image size is suspiciously small (possible mock/error?)")
            else:
                logger.error(f"❌ Image file missing at {physical_image_path}")
                
        else:
            logger.error(f"❌ Workflow failed: {result.error}")
            
    except Exception as e:
        logger.error(f"❌ Verification failed with exception: {e}")

if __name__ == "__main__":
    asyncio.run(main())
