#!/usr/bin/env python3
"""
Test script for Foundry Agent Service Client (POC)

This script demonstrates how to use the FoundryAgentServiceClient
for thread management. Run this in development to test Foundry integration.

Usage:
    python scripts/test_foundry_client.py

Prerequisites:
    - Set environment variables:
      - AZURE_FOUNDRY_AGENT_ENDPOINT
      - AZURE_FOUNDRY_AGENT_PROJECT
      - AZURE_FOUNDRY_AGENT_KEY (optional, uses Managed Identity if not set)
    - Enable feature flag: USE_FOUNDRY_THREADS=true (for testing only)
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.agents.foundry_client import FoundryAgentServiceClient, get_foundry_client
from backend.core import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_thread_management():
    """Test Foundry thread creation and message management."""
    logger.info("=" * 60)
    logger.info("Testing Foundry Agent Service Thread Management")
    logger.info("=" * 60)
    
    # Check if Foundry is configured
    settings = get_settings()
    if not settings.azure_foundry_agent_endpoint or not settings.azure_foundry_agent_project:
        logger.error("Foundry Agent Service not configured!")
        logger.error("Set AZURE_FOUNDRY_AGENT_ENDPOINT and AZURE_FOUNDRY_AGENT_PROJECT")
        return False
    
    # Get client
    client = get_foundry_client()
    if not client:
        logger.error("Failed to initialize Foundry client")
        logger.error("Check configuration and ensure feature flags are enabled")
        return False
    
    try:
        # Test 1: Create a thread
        logger.info("\n[Test 1] Creating thread...")
        thread_id = await client.create_thread(
            user_id="test-user-123",
            agent_id="elena",
            project_id="test-project",
            metadata={"test": True, "poc": True},
        )
        logger.info(f"✅ Created thread: {thread_id}")
        
        # Test 2: Get thread details
        logger.info("\n[Test 2] Getting thread details...")
        thread = await client.get_thread(thread_id)
        logger.info(f"✅ Retrieved thread: {thread.get('id', 'unknown')}")
        logger.info(f"   Metadata: {thread.get('metadata', {})}")
        
        # Test 3: Add messages
        logger.info("\n[Test 3] Adding messages...")
        user_msg = await client.add_message(
            thread_id=thread_id,
            role="user",
            content="Hello, this is a test message from the POC.",
        )
        logger.info(f"✅ Added user message: {user_msg.get('id', 'unknown')}")
        
        assistant_msg = await client.add_message(
            thread_id=thread_id,
            role="assistant",
            content="Hello! I'm Elena, and I'm here to help with your requirements.",
        )
        logger.info(f"✅ Added assistant message: {assistant_msg.get('id', 'unknown')}")
        
        # Test 4: List messages
        logger.info("\n[Test 4] Listing messages...")
        messages = await client.list_messages(thread_id, limit=10)
        logger.info(f"✅ Retrieved {len(messages)} messages")
        for i, msg in enumerate(messages, 1):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:50]
            logger.info(f"   {i}. [{role}] {content}...")
        
        # Test 5: List threads
        logger.info("\n[Test 5] Listing threads...")
        threads = await client.list_threads(
            user_id="test-user-123",
            agent_id="elena",
            limit=10,
        )
        logger.info(f"✅ Found {len(threads)} threads")
        for i, thread in enumerate(threads, 1):
            tid = thread.get("id", "unknown")
            metadata = thread.get("metadata", {})
            logger.info(f"   {i}. Thread {tid[:20]}... (agent: {metadata.get('agent_id', 'unknown')})")
        
        # Test 6: Cleanup (optional - comment out to keep thread)
        logger.info("\n[Test 6] Cleaning up...")
        cleanup = os.getenv("FOUNDRY_TEST_CLEANUP", "false").lower() == "true"
        if cleanup:
            await client.delete_thread(thread_id)
            logger.info(f"✅ Deleted thread: {thread_id}")
        else:
            logger.info(f"⏭️  Skipping cleanup (set FOUNDRY_TEST_CLEANUP=true to enable)")
            logger.info(f"   Thread ID: {thread_id}")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ All tests passed!")
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}", exc_info=True)
        return False


async def test_feature_flags():
    """Test that feature flags work correctly."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Feature Flags")
    logger.info("=" * 60)
    
    settings = get_settings()
    
    logger.info(f"USE_FOUNDRY_THREADS: {settings.use_foundry_threads}")
    logger.info(f"USE_FOUNDRY_FILES: {settings.use_foundry_files}")
    logger.info(f"USE_FOUNDRY_VECTORS: {settings.use_foundry_vectors}")
    logger.info(f"USE_FOUNDRY_TOOLS: {settings.use_foundry_tools}")
    
    # Test that client returns None when flags are disabled
    if not settings.use_foundry_threads and not settings.use_foundry_files:
        client = get_foundry_client()
        if client is None:
            logger.info("✅ Client correctly returns None when flags are disabled")
        else:
            logger.warning("⚠️  Client initialized even though flags are disabled")
    else:
        logger.info("ℹ️  Feature flags are enabled - client will be initialized")
    
    logger.info("=" * 60)


async def main():
    """Main test function."""
    logger.info("Foundry Agent Service Client POC Test")
    logger.info("=" * 60)
    
    # Test feature flags first
    await test_feature_flags()
    
    # Test thread management if configured
    if os.getenv("AZURE_FOUNDRY_AGENT_ENDPOINT") and os.getenv("AZURE_FOUNDRY_AGENT_PROJECT"):
        success = await test_thread_management()
        sys.exit(0 if success else 1)
    else:
        logger.warning("\n⚠️  Foundry not configured - skipping thread management tests")
        logger.warning("Set AZURE_FOUNDRY_AGENT_ENDPOINT and AZURE_FOUNDRY_AGENT_PROJECT to test")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())

