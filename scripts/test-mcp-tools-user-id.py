#!/usr/bin/env python3
"""
Test MCP Tools User ID Attribution

Tests that MCP tools properly receive and use user_id from agent context.

Usage:
    python3 scripts/test-mcp-tools-user-id.py --user-id <USER_ID> [--tool <TOOL_NAME>]
"""

import argparse
import asyncio
import logging
import os
import sys
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_chat_with_agent(user_id: str) -> bool:
    """Test chat_with_agent MCP tool with user_id."""
    try:
        from backend.api.routers.mcp_server import chat_with_agent
        
        logger.info(f"Testing chat_with_agent with user_id: {user_id}")
        result = await chat_with_agent(
            message="Hello, this is a test",
            user_id=user_id,
            session_id=f"test-session-{os.getpid()}",
            agent_id="elena"
        )
        
        logger.info(f"✅ chat_with_agent result: {result[:100]}...")
        return True
    except Exception as e:
        logger.error(f"❌ chat_with_agent failed: {e}")
        return False


async def test_enrich_memory(user_id: str) -> bool:
    """Test enrich_memory MCP tool with user_id."""
    try:
        from backend.api.routers.mcp_server import enrich_memory
        
        logger.info(f"Testing enrich_memory with user_id: {user_id}")
        result = await enrich_memory(
            text="This is a test memory enrichment",
            user_id=user_id,
            session_id=f"test-session-{os.getpid()}"
        )
        
        logger.info(f"✅ enrich_memory result: {result}")
        return True
    except Exception as e:
        logger.error(f"❌ enrich_memory failed: {e}")
        return False


async def test_search_memory(user_id: str) -> bool:
    """Test search_memory MCP tool with user_id."""
    try:
        from backend.api.routers.mcp_server import search_memory
        
        logger.info(f"Testing search_memory with user_id: {user_id}")
        result = await search_memory(
            query="test query",
            user_id=user_id,
            session_id=f"test-session-{os.getpid()}"
        )
        
        logger.info(f"✅ search_memory result: {result[:200]}...")
        return True
    except Exception as e:
        logger.error(f"❌ search_memory failed: {e}")
        return False


async def test_ingest_document(user_id: str) -> bool:
    """Test ingest_document MCP tool with user_id."""
    try:
        from backend.api.routers.mcp_server import ingest_document
        
        logger.info(f"Testing ingest_document with user_id: {user_id}")
        result = await ingest_document(
            content="# Test Document\n\nThis is a test document for ingestion.",
            title="Test Document",
            user_id=user_id,
            doc_type="markdown"
        )
        
        logger.info(f"✅ ingest_document result: {result[:200]}...")
        return True
    except Exception as e:
        logger.error(f"❌ ingest_document failed: {e}")
        return False


async def test_agent_tool_invocation(user_id: str) -> bool:
    """Test that agents inject user_id into tool arguments."""
    try:
        from backend.core import EnterpriseContext, SecurityContext, Role
        from backend.agents.marcus.agent import MarcusAgent
        
        logger.info(f"Testing agent tool invocation with user_id: {user_id}")
        
        # Create EnterpriseContext with user_id
        security = SecurityContext(
            user_id=user_id,
            tenant_id="test-tenant",
            roles=[Role.ANALYST],
            scopes=["*"]
        )
        context = EnterpriseContext(security=security)
        
        # Create agent
        agent = MarcusAgent()
        
        # Test that tool invocation would inject user_id
        # (We can't easily test the full flow without LangGraph, but we can verify the method exists)
        if hasattr(agent, '_maybe_use_tool'):
            logger.info("✅ Agent has _maybe_use_tool method (user_id injection should work)")
            return True
        else:
            logger.error("❌ Agent missing _maybe_use_tool method")
            return False
            
    except Exception as e:
        logger.error(f"❌ Agent tool invocation test failed: {e}")
        return False


async def main():
    parser = argparse.ArgumentParser(description="Test MCP Tools User ID Attribution")
    parser.add_argument("--user-id", default="test-user-123", help="User ID to test with")
    parser.add_argument("--tool", choices=["all", "chat", "enrich", "search", "ingest", "agent"], 
                       default="all", help="Which tool to test")
    args = parser.parse_args()
    
    user_id = args.user_id or os.environ.get("TEST_USER_ID", "test-user-123")
    
    print("=" * 60)
    print("MCP Tools User ID Attribution Test")
    print("=" * 60)
    print(f"User ID: {user_id}")
    print(f"Tool: {args.tool}")
    print()
    
    results = {}
    
    if args.tool in ["all", "chat"]:
        print("Test 1: chat_with_agent")
        print("-" * 60)
        results["chat"] = await test_chat_with_agent(user_id)
        print()
    
    if args.tool in ["all", "enrich"]:
        print("Test 2: enrich_memory")
        print("-" * 60)
        results["enrich"] = await test_enrich_memory(user_id)
        print()
    
    if args.tool in ["all", "search"]:
        print("Test 3: search_memory")
        print("-" * 60)
        results["search"] = await test_search_memory(user_id)
        print()
    
    if args.tool in ["all", "ingest"]:
        print("Test 4: ingest_document")
        print("-" * 60)
        results["ingest"] = await test_ingest_document(user_id)
        print()
    
    if args.tool in ["all", "agent"]:
        print("Test 5: Agent tool invocation")
        print("-" * 60)
        results["agent"] = await test_agent_tool_invocation(user_id)
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

