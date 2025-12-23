"""
Temporal Worker

The worker runs workflows and activities.
Deploy multiple workers for scalability and fault tolerance.
"""

import asyncio
import logging
import signal
import sys

from temporalio.client import Client
from temporalio.worker import Worker

from backend.core import get_settings
from backend.workflows.activities import (
    agent_reasoning_activity,
    enrich_memory_activity,
    execute_tool_activity,
    initialize_context_activity,
    persist_memory_activity,
    send_notification_activity,
    validate_response_activity,
)
from backend.workflows.story_activities import (
    generate_story_activity,
    generate_diagram_activity,
    save_artifacts_activity,
    enrich_story_memory_activity,
)
from backend.workflows.agent_workflow import (
    AgentWorkflow,
    ApprovalWorkflow,
    ConversationWorkflow,
)
from backend.workflows.story_workflow import StoryWorkflow

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def create_temporal_client() -> Client:
    """Create a Temporal client with Azure Container Apps support"""
    settings = get_settings()

    # Parse host and port
    host_parts = settings.temporal_host.split(":")
    host = host_parts[0]
    port = int(host_parts[1]) if len(host_parts) > 1 else 7233

    logger.info(f"Connecting to Temporal at {host}:{port}")

    # Azure Container Apps internal ingress uses TLS on port 443
    # For port 443, we need TLS enabled
    use_tls = port == 443 or ".azurecontainerapps.io" in host
    
    if use_tls:
        logger.info("Using TLS for Azure Container Apps connection")
        client = await Client.connect(
            f"{host}:{port}",
            namespace=settings.temporal_namespace,
            tls=True,  # Enable TLS for Azure internal ingress
        )
    else:
        client = await Client.connect(
            f"{host}:{port}",
            namespace=settings.temporal_namespace,
        )

    logger.info(f"Connected to Temporal namespace: {settings.temporal_namespace}")
    return client


async def run_worker():
    """Run the Temporal worker"""
    settings = get_settings()

    # Create client
    client = await create_temporal_client()

    # Create worker
    worker = Worker(
        client,
        task_queue=settings.temporal_task_queue,
        workflows=[
            AgentWorkflow,
            ConversationWorkflow,
            ApprovalWorkflow,
            StoryWorkflow,
        ],
        activities=[
            initialize_context_activity,
            enrich_memory_activity,
            agent_reasoning_activity,
            persist_memory_activity,
            execute_tool_activity,
            send_notification_activity,
            validate_response_activity,
            # Story activities
            generate_story_activity,
            generate_diagram_activity,
            save_artifacts_activity,
            enrich_story_memory_activity,
        ],
    )

    logger.info(f"Starting worker on task queue: {settings.temporal_task_queue}")

    # Handle shutdown gracefully
    shutdown_event = asyncio.Event()

    def handle_shutdown(sig):
        logger.info(f"Received {sig}, shutting down...")
        shutdown_event.set()

    # Register signal handlers
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: handle_shutdown(s))

    # Run worker until shutdown
    async with worker:
        logger.info("Worker started successfully")
        await shutdown_event.wait()

    logger.info("Worker shut down")


def main():
    """Entry point for the worker"""
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Worker interrupted")
    except Exception as e:
        logger.exception("Worker failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
