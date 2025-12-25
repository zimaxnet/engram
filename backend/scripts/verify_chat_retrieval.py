#!/usr/bin/env python3
"""
Verify Chat Retrieval CLI - Attempt 2

This script verifies that the agent can retrieve the recently ingested
Agentic System Framework and Maturity Assessment from Azure Zep.
"""

import os
import sys

# 1. SET ENVIRONMENT VARIABLES BEFORE IMPORTS
os.environ["ZEP_API_URL"] = "https://zep.engram.work"
os.environ["ENVIRONMENT"] = "production" # To ensure it doesn't try local mocks if any existed

# Add project root to path
sys.path.append(os.getcwd())

import asyncio
import logging
from datetime import datetime

# Clear settings cache if any
from backend.core.config import get_settings
get_settings.cache_clear()

from backend.agents import chat
from backend.core import EnterpriseContext, SecurityContext, Role
from backend.memory import enrich_context

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def test_retrieval(query: str, agent_id: str = "elena"):
    print(f"\n{'='*60}")
    print(f"TESTING RETRIEVAL FOR: \"{query}\"")
    print(f"AGENT: {agent_id}")
    print(f"{'='*60}")

    # 1. Setup Security Context
    security = SecurityContext(
        user_id="cli-tester",
        tenant_id="engram-dev",
        roles=[Role.ADMIN],
        scopes=["*"]
    )

    # 2. Setup Enterprise Context
    context = EnterpriseContext(security=security)
    context.episodic.conversation_id = f"test-cli-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    # 3. Step 1: Manual Context Enrichment
    print(f"\n🔍 Step 1: Triggering Context Enrichment...")
    try:
        # Check Zep URL being used
        settings = get_settings()
        print(f"ℹ️  Using Zep URL: {settings.zep_api_url}")
        
        enriched_context = await enrich_context(context, query)
        
        # Check semantic knowledge (Corrected attribute names)
        # Layer 3 is context.semantic
        # Graph nodes are in context.semantic.retrieved_facts
        facts = enriched_context.semantic.retrieved_facts
        
        if facts:
            print(f"✅ Retrieved {len(facts)} knowledge items from Zep!")
            for i, fact in enumerate(facts):
                preview = fact.content[:150].replace('\n', ' ')
                print(f"   [{i+1}] {preview}...")
        else:
            print("⚠️ No semantic knowledge/facts retrieved for this query.")
            
    except Exception as e:
        print(f"❌ Enrichment failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # 4. Step 2: Agent Chat 
    print(f"\n💬 Step 2: Running Agent Chat Loop...")
    try:
        response_text, updated_context, actual_agent_id = await chat(
            query=query,
            context=enriched_context,
            agent_id=agent_id
        )
        
        print(f"\n{'='*60}")
        print(f"RESPONSE FROM {actual_agent_id.upper()}:")
        print(f"{'='*60}")
        print(response_text)
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"❌ Chat failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    # Test 1: Framework Layers
    await test_retrieval("What are the 7 layers of the Production-Grade Agentic System framework?")
    
    # Test 2: Maturity Score (Testing more specific retrieval)
    await test_retrieval("According to our maturity assessment, what is our score for Layer 6 and what are the critical gaps?")

if __name__ == "__main__":
    asyncio.run(main())
