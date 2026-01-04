from datetime import timedelta
from temporalio import activity, workflow

@activity.defn
async def repair_stories_activity() -> str:
    """
    Activity that runs the repair_stories logic from the script.
    """
    import logging
    # Import the logic function from the script
    from backend.scripts.repair_story_images import repair_stories
    
    logger = logging.getLogger(__name__)
    logger.info("Starting story image repair activity...")
    
    try:
        # Run the repair logic
        await repair_stories()
        return "Repair process completed successfully"
    except Exception as e:
        logger.error(f"Repair process failed: {e}")
        raise

@workflow.defn
class RepairWorkflow:
    @workflow.run
    async def run(self) -> str:
        return await workflow.execute_activity(
            repair_stories_activity,
            start_to_close_timeout=timedelta(minutes=60)
        )
