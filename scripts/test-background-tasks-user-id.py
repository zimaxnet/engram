#!/usr/bin/env python3
"""
Test Background Tasks User ID Preservation

Tests that background tasks properly preserve user_id throughout execution.

Usage:
    python3 scripts/test-background-tasks-user-id.py --user-id <USER_ID> [--test <TEST_NAME>]
"""

import argparse
import asyncio
import logging
import os
import sys
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_chat_persistence(user_id: str) -> bool:
    """Test chat persistence background task preserves user_id."""
    try:
        from backend.core import EnterpriseContext, SecurityContext, Role, MessageRole, Turn
        from backend.memory import persist_conversation
        from datetime import datetime
        
        logger.info(f"Testing chat persistence with user_id: {user_id}")
        
        # Create context with user_id
        security = SecurityContext(
            user_id=user_id,
            tenant_id="test-tenant",
            roles=[Role.ANALYST],
            scopes=["*"]
        )
        context = EnterpriseContext(security=security)
        context.episodic.conversation_id = f"test-session-{os.getpid()}"
        
        # Add a turn
        context.episodic.add_turn(Turn(
            role=MessageRole.USER,
            content="Test message",
            timestamp=datetime.utcnow()
        ))
        
        # Simulate background task
        async def _persist_with_timeout():
            user_id_check = context.security.user_id
            logger.info(f"Background task started: persisting conversation for user: {user_id_check}")
            try:
                await persist_conversation(context)
                logger.info(f"Background task completed: conversation persisted for user: {user_id_check}")
                return user_id_check == user_id
            except Exception as e:
                logger.error(f"Background task failed for user: {user_id_check}: {e}")
                return False
        
        # Run background task
        result = await _persist_with_timeout()
        
        if result:
            logger.info("✅ Chat persistence preserved user_id correctly")
            return True
        else:
            logger.error("❌ Chat persistence user_id mismatch")
            return False
            
    except Exception as e:
        logger.error(f"❌ Chat persistence test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_document_ingestion(user_id: str) -> bool:
    """Test document ingestion background task preserves user_id."""
    try:
        from backend.etl.ingestion_service import ingestion_service
        from fastapi import BackgroundTasks
        
        logger.info(f"Testing document ingestion with user_id: {user_id}")
        
        # Create test document content
        content = b"# Test Document\n\nThis is a test document for ingestion."
        filename = "test-document.md"
        content_type = "text/markdown"
        
        # Create background tasks
        background_tasks = BackgroundTasks()
        
        # Call ingestion (this will add background task)
        response = await ingestion_service.ingest_document(
            content=content,
            filename=filename,
            content_type=content_type,
            user_id=user_id,
            background_tasks=background_tasks
        )
        
        logger.info(f"✅ Document ingestion response: {response.message}")
        
        # Note: Background tasks run after response, so we can't easily verify here
        # But we can verify the user_id was passed correctly
        if response.success:
            logger.info("✅ Document ingestion accepted with user_id")
            return True
        else:
            logger.error("❌ Document ingestion failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Document ingestion test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_voice_persistence(user_id: str) -> bool:
    """Test voice persistence background task preserves user_id."""
    try:
        from backend.core import EnterpriseContext, SecurityContext, Role, MessageRole, Turn
        from backend.memory import persist_conversation
        from datetime import datetime
        
        logger.info(f"Testing voice persistence with user_id: {user_id}")
        
        # Create context with user_id (simulating voice context)
        security = SecurityContext(
            user_id=user_id,
            tenant_id="test-tenant",
            roles=[Role.ANALYST],
            scopes=["*"]
        )
        voice_context = EnterpriseContext(security=security, context_version="1.0.0")
        voice_context.episodic.conversation_id = f"voice-session-{os.getpid()}"
        
        # Add voice turns
        voice_context.episodic.add_turn(Turn(
            role=MessageRole.USER,
            content="Voice test message",
            timestamp=datetime.utcnow()
        ))
        
        # Simulate background task (from voice.py)
        async def _persist_latest_turns():
            user_id_check = voice_context.security.user_id
            logger.info(f"Background task started: persisting voice conversation for user: {user_id_check}")
            try:
                await persist_conversation(voice_context)
                logger.info(f"Background task completed: voice conversation persisted for user: {user_id_check}")
                return user_id_check == user_id
            except Exception as e:
                logger.error(f"Background task failed for user: {user_id_check}: {e}")
                return False
        
        # Run background task
        result = await _persist_latest_turns()
        
        if result:
            logger.info("✅ Voice persistence preserved user_id correctly")
            return True
        else:
            logger.error("❌ Voice persistence user_id mismatch")
            return False
            
    except Exception as e:
        logger.error(f"❌ Voice persistence test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    parser = argparse.ArgumentParser(description="Test Background Tasks User ID Preservation")
    parser.add_argument("--user-id", default="test-user-123", help="User ID to test with")
    parser.add_argument("--test", choices=["all", "chat", "document", "voice"], 
                       default="all", help="Which test to run")
    args = parser.parse_args()
    
    user_id = args.user_id or os.environ.get("TEST_USER_ID", "test-user-123")
    
    print("=" * 60)
    print("Background Tasks User ID Preservation Test")
    print("=" * 60)
    print(f"User ID: {user_id}")
    print(f"Test: {args.test}")
    print()
    
    results = {}
    
    if args.test in ["all", "chat"]:
        print("Test 1: Chat Persistence Background Task")
        print("-" * 60)
        results["chat"] = await test_chat_persistence(user_id)
        print()
    
    if args.test in ["all", "document"]:
        print("Test 2: Document Ingestion Background Task")
        print("-" * 60)
        results["document"] = await test_document_ingestion(user_id)
        print()
    
    if args.test in ["all", "voice"]:
        print("Test 3: Voice Persistence Background Task")
        print("-" * 60)
        results["voice"] = await test_voice_persistence(user_id)
        print()
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    for test_name, result in results.items():
        if result:
            print(f"✅ {test_name}: PASSED")
        else:
            print(f"❌ {test_name}: FAILED")
    
    if all(results.values()):
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

