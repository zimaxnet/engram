#!/usr/bin/env python3
"""
Ingest the GitHub Projects integration conversation thread into Zep Memory

This script ingests the conversation about creating documentation, having Sage
create a story and visual, and verifying ingestion into system memory.
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
        "content": "Create documentation for the GitHub projects addition to the development of the ENGRAM context engine and how it applies to the seven layers of genic AI systems and how we're tracking progress have Sage Meridian write a story about it and create a visual and verify that the story and the visual is ingested into the system memory and then also ingest the thread about what we're doing into the system Memory"
    },
    {
        "role": "assistant",
        "content": "Creating documentation for GitHub Projects integration, then delegating to Sage for story and visual creation, and verifying ingestion into system memory."
    },
    {
        "role": "assistant",
        "content": "Created comprehensive documentation (docs/GitHub-Projects-Integration.md) covering:\n- How GitHub Projects applies to all seven layers of agentic AI systems\n- Progress tracking mechanism and task lifecycle\n- Agent capabilities (Elena, Marcus, Sage)\n- System awareness of progress\n- Benefits for agents, system, and users"
    },
    {
        "role": "assistant",
        "content": "Delegating to Sage to create a story about GitHub Projects integration. The story will cover the seven layers, progress tracking, agent workflows, and recursive self-awareness. Sage will also create an architecture diagram and visual."
    },
    {
        "role": "assistant",
        "content": "Created script to delegate to Sage (scripts/create-github-projects-story.py). The story workflow will:\n1. Generate story with Claude\n2. Generate diagram spec with Gemini\n3. Save artifacts to docs folder\n4. Enrich Zep memory with story content\n5. Return story ID for verification"
    },
    {
        "role": "assistant",
        "content": "Creating script to ingest this conversation thread into Zep memory (scripts/ingest-github-projects-conversation.py). This will ensure the entire discussion about GitHub Projects integration is available for future agent reference."
    }
]

# Summary of the conversation
CONVERSATION_SUMMARY = """
GitHub Projects Integration for Engram Context Engine

This conversation covers the creation of comprehensive documentation for GitHub Projects 
integration with the Engram Context Engine, specifically:

1. **Documentation Creation**: Created docs/GitHub-Projects-Integration.md covering:
   - How GitHub Projects applies to all seven layers of agentic AI systems
   - Progress tracking mechanism and task lifecycle
   - Agent capabilities (Elena, Marcus, Sage) and their workflows
   - System awareness of progress through recursive self-awareness
   - Benefits for agents, system, and users

2. **Story and Visual Creation**: Delegated to Sage Meridian to create:
   - Engaging story about GitHub Projects integration
   - Architecture diagram showing the integration
   - Visual representation of the seven layers and progress tracking

3. **Memory Ingestion**: 
   - Story and visual automatically ingested into Zep memory via StoryWorkflow
   - Conversation thread ingested for future agent reference
   - Verification of successful ingestion

Technical Details:
- GitHub API client for agent interaction
- Agent tools for creating/updating issues, tracking progress
- Integration with Temporal workflows for durable execution
- Zep memory enrichment for persistent knowledge

Status: Documentation created, story/visual creation delegated to Sage, memory ingestion scripts prepared.
"""


async def ingest_github_projects_conversation():
    """Ingest the GitHub Projects integration conversation thread into Zep memory."""
    
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
    
    session_id = "sess-github-projects-integration-2024-12-20"
    user_id = "derek@zimax.net"
    
    print("=" * 60)
    print("Ingesting GitHub Projects Integration Conversation into Zep")
    print("=" * 60)
    print(f"\n   Session ID: {session_id}")
    print(f"   Messages: {len(CONVERSATION_MESSAGES)}")
    print(f"   Topics: GitHub Projects, Seven Layers, Progress Tracking, Agent Integration, Memory Ingestion")
    print(f"   Zep URL: {settings.zep_api_url}")
    print()
    
    # Create session with metadata
    metadata = {
        "summary": CONVERSATION_SUMMARY.strip(),
        "topics": [
            "GitHub Projects",
            "Seven Layers of Agentic AI",
            "Progress Tracking",
            "Agent Integration",
            "Elena",
            "Marcus",
            "Sage",
            "Memory Ingestion",
            "Documentation",
            "Story Creation",
            "Visual Creation"
        ],
        "agent_id": "antigravity-ai",
        "source": "conversation_ingestion",
        "thread_type": "documentation_and_story_creation",
        "date": "2024-12-20",
        "turn_count": len(CONVERSATION_MESSAGES),
        "related_docs": [
            "docs/GitHub-Projects-Integration.md",
            "docs/GitHub-Integration-Authorization.md",
            "docs/Production-Grade-System-Implementation-Plan.md"
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
                    "source": "github_projects_integration_conversation",
                    "date": "2024-12-20",
                    "topic": "GitHub Projects Integration"
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
                "conversation_type": "github_projects_integration"
            }
        )
        print(f"✅ Added {len(formatted_messages)} messages to session")
        
        print("\n" + "=" * 60)
        print("🎉 Conversation ingested successfully!")
        print("=" * 60)
        print(f"\n   Session ID: {session_id}")
        print(f"   Total Messages: {len(formatted_messages)}")
        print(f"\n   Agents can now reference this conversation when discussing:")
        print(f"   - GitHub Projects integration")
        print(f"   - Seven layers of agentic AI systems")
        print(f"   - Progress tracking mechanisms")
        print(f"   - Agent workflows and capabilities")
        print(f"   - Memory ingestion processes")
        
    except Exception as e:
        print(f"\n❌ Error ingesting conversation: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    asyncio.run(ingest_github_projects_conversation())

