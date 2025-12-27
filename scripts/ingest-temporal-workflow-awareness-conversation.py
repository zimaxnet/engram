#!/usr/bin/env python3
"""
Ingest the Temporal Workflow Awareness conversation thread into Zep Memory

This script ingests the conversation about making Elena and Marcus aware
that delegating to Sage initiates a Temporal workflow.
"""

import asyncio
import sys
from pathlib import Path
import os
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.memory.client import ZepMemoryClient
from backend.core import get_settings

# Conversation thread content
CONVERSATION_MESSAGES = [
    {
        "role": "user",
        "content": "Alina needs to be aware that whenever she does delegate the story and visual creation to Sage that she is initiating adorable workflow to be executed via temporal. Is that happening in this system?"
    },
    {
        "role": "assistant",
        "content": "Checking Elena's system prompt and the delegate_to_sage tool to ensure she's aware she's initiating a Temporal workflow."
    },
    {
        "role": "assistant",
        "content": "Elena knows about Temporal ('The Spine'), but the delegate_to_sage tool description doesn't explicitly mention it initiates a Temporal workflow. Updating the tool description and system prompt to make this explicit."
    },
    {
        "role": "assistant",
        "content": "Updated delegate_to_sage tool descriptions for both Elena and Marcus to explicitly mention Temporal workflow. Added details about StoryWorkflow durability and observability. Updated system prompts to explain delegation creates durable workflows. Added section explaining workflow benefits (durability, observability, auto-save)."
    },
    {
        "role": "assistant",
        "content": "Now Elena and Marcus are fully aware that when they delegate to Sage, they are initiating a durable Temporal workflow that can be monitored and will survive interruptions."
    }
]

# Summary of the conversation
CONVERSATION_SUMMARY = """
Temporal Workflow Awareness for Agent Delegation

This conversation covers making Elena and Marcus agents aware that when they
delegate story and visual creation to Sage, they are initiating a durable
Temporal workflow (StoryWorkflow).

Key Changes Made:
1. **Tool Description Updates**: Updated `delegate_to_sage` tool descriptions
   for both Elena and Marcus to explicitly mention:
   - Initiates a Temporal workflow (StoryWorkflow)
   - Workflow is durable and observable
   - Orchestrates complete story creation process
   - Artifacts automatically saved and ingested

2. **System Prompt Updates**: Added "Delegation to Sage" section to both
   agents' system prompts explaining:
   - Delegation creates a Temporal workflow
   - Workflow benefits (durability, observability)
   - Agents can explain the process to users
   - Workflow can be monitored in Temporal UI

3. **Agent Awareness**: Both Elena and Marcus now understand:
   - They initiate Temporal workflows when delegating
   - Workflows are durable (survive restarts/interruptions)
   - Workflows are observable (progress can be monitored)
   - They can explain the workflow process to users

Technical Details:
- StoryWorkflow orchestrates: story generation (Claude), diagram creation (Gemini), visual generation
- Workflow ensures durability and provides observability
- All artifacts automatically saved to docs/stories/ and ingested into Zep memory
- Workflow ID returned for tracking and monitoring

Status: Complete - Both agents are now fully aware of Temporal workflow initiation when delegating to Sage.
"""


async def ingest_temporal_workflow_awareness_conversation():
    """Ingest the Temporal Workflow Awareness conversation thread into Zep memory."""
    
    zep_url = os.getenv("ZEP_API_URL")
    if not zep_url:
        settings = get_settings()
        zep_url = settings.zep_api_url
    
    if not zep_url:
        print("❌ ZEP_API_URL not configured")
        print("   Set ZEP_API_URL environment variable")
        print("   Example: export ZEP_API_URL=https://zep-app.internal:8000")
        return False
    
    # Temporarily override settings for this script
    settings = get_settings()
    if zep_url:
        settings.zep_api_url = zep_url
    
    client = ZepMemoryClient()
    
    session_id = "sess-temporal-workflow-awareness-2024-12-20"
    user_id = "derek@zimax.net"
    
    print("=" * 60)
    print("Ingesting Temporal Workflow Awareness Conversation into Zep")
    print("=" * 60)
    print(f"\n   Session ID: {session_id}")
    print(f"   Messages: {len(CONVERSATION_MESSAGES)}")
    print(f"   Topics: Temporal Workflows, Agent Delegation, Elena, Marcus, Sage, StoryWorkflow, Durable Execution, Observability")
    print(f"   Zep URL: {settings.zep_api_url}")
    print()
    
    # Create session with metadata
    metadata = {
        "summary": CONVERSATION_SUMMARY.strip(),
        "topics": [
            "Temporal Workflows",
            "Agent Delegation",
            "Elena",
            "Marcus",
            "Sage",
            "StoryWorkflow",
            "Durable Execution",
            "Observability",
            "Agent Awareness",
            "System Architecture"
        ],
        "agent_id": "antigravity-ai",
        "source": "conversation_ingestion",
        "thread_type": "agent_awareness_enhancement",
        "date": "2024-12-20",
        "turn_count": len(CONVERSATION_MESSAGES),
        "related_docs": [
            "backend/agents/elena/agent.py",
            "backend/agents/marcus/agent.py",
            "backend/workflows/story_workflow.py"
        ],
        "key_changes": [
            "Updated delegate_to_sage tool descriptions",
            "Added Delegation to Sage section to system prompts",
            "Enhanced agent awareness of Temporal workflows"
        ]
    }
    
    try:
        # Create or get session
        print("📝 Creating/getting Zep session...")
        session = await client.get_or_create_session(
            session_id=session_id,
            user_id=user_id,
            metadata=metadata
        )
        print(f"   ✅ Session created/retrieved: {session_id}")
        
        # Format messages for Zep
        formatted_messages = []
        for msg in CONVERSATION_MESSAGES:
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["content"],
                "metadata": {
                    "source": "temporal_workflow_awareness_conversation",
                    "date": "2024-12-20",
                    "topic": "Agent Temporal Workflow Awareness"
                }
            })
        
        # Add messages to session
        print(f"💾 Adding {len(formatted_messages)} messages to session...")
        await client.add_memory(
            session_id=session_id,
            messages=formatted_messages,
            metadata={
                "ingested_at": datetime.now(timezone.utc).isoformat(),
                "source": "script_ingestion",
                "conversation_type": "temporal_workflow_awareness"
            }
        )
        print(f"✅ Added {len(formatted_messages)} messages to session")
        
        # Enrich memory with key concepts
        print("\n🧠 Enriching memory with key concepts...")
        enrichment_messages = [
            {
                "role": "system",
                "content": "Key Concept: When Elena or Marcus delegates to Sage using delegate_to_sage, they initiate a durable Temporal workflow (StoryWorkflow) that orchestrates story generation, diagram creation, and visual generation. This workflow is observable and can be monitored for progress."
            },
            {
                "role": "system",
                "content": "Key Concept: StoryWorkflow ensures durability - the task will complete even if there are server restarts or network interruptions. All artifacts are automatically saved and ingested into Zep memory."
            },
            {
                "role": "system",
                "content": "Key Concept: Both Elena and Marcus are now aware that delegation creates Temporal workflows and can explain this process to users when asked about how story creation works."
            }
        ]
        
        await client.add_memory(
            session_id=session_id,
            messages=enrichment_messages,
            metadata={
                "ingested_at": datetime.now(timezone.utc).isoformat(),
                "source": "memory_enrichment",
                "type": "key_concepts"
            }
        )
        print("✅ Memory enriched with key concepts")
        
        print("\n" + "=" * 60)
        print("🎉 Conversation ingested and memory enriched successfully!")
        print("=" * 60)
        print(f"\n   Session ID: {session_id}")
        print(f"   Total Messages: {len(formatted_messages) + len(enrichment_messages)}")
        print(f"\n   Agents can now reference this conversation when discussing:")
        print(f"   - Temporal workflow initiation via delegation")
        print(f"   - StoryWorkflow durability and observability")
        print(f"   - Agent awareness of workflow orchestration")
        print(f"   - How delegation creates durable workflows")
        
    except Exception as e:
        print(f"\n❌ Error ingesting conversation: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    asyncio.run(ingest_temporal_workflow_awareness_conversation())

