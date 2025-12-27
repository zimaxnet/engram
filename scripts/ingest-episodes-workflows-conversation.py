#!/usr/bin/env python3
"""
Ingest the episodes and workflows conversation thread into Zep memory.

This script ingests the conversation about:
- Episodes feature development (filtering, search, pagination)
- Workflow visibility enhancements (Elena → Sage delegations)
- Sessions vs Episodes vs Workflows clarification

The conversation will be stored as a session in Zep so agents can reference it.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.memory.client import ZepMemoryClient
from backend.core import get_settings


async def ingest_conversation():
    """Ingest the episodes and workflows conversation into Zep."""
    
    settings = get_settings()
    client = ZepMemoryClient()
    
    # Session ID for this conversation
    session_id = "sess-episodes-workflows-2024-12-20"
    
    # Conversation summary
    summary = """Development of Episodes feature and Workflow visibility enhancements.
    
Key topics:
- Episodes page enhancements (filtering, search, pagination, UI/UX)
- Workflow visibility for Elena → Sage delegations
- Clarification of Sessions vs Episodes vs Workflows concepts
- Temporal workflow observability implementation"""
    
    # Topics
    topics = [
        "Episodes",
        "Workflows",
        "Sessions",
        "Zep Memory",
        "Temporal",
        "Frontend Development",
        "Backend API",
        "UI/UX",
        "Delegation",
        "Observability"
    ]
    
    # Conversation messages
    messages = [
        {
            "role": "user",
            "content": "Developed the optional enhancements and then will commit pushing test",
            "metadata": {
                "timestamp": "2024-12-20T10:00:00Z",
                "context": "Requesting implementation of Episodes page enhancements"
            }
        },
        {
            "role": "assistant",
            "content": """I've implemented all the optional enhancements for the Episodes feature:

## Episodes Enhancements Complete

### Implemented Features

1. **Filtering and Search**
   - Text search across summaries and topics
   - Filter by agent (Elena, Marcus, Sage, All)
   - Filter by topic (dynamic dropdown from available topics)
   - Date range filtering (from/to dates)
   - Clear filters button

2. **Pagination**
   - 10 episodes per page
   - Previous/Next navigation
   - Page counter (Page X of Y)
   - Disabled states for first/last page

3. **UI/UX Improvements**
   - Loading spinner with animation
   - Error messages with retry button
   - Skeleton loaders for transcript loading
   - Hover effects on episode cards
   - Responsive filter grid layout
   - Improved modal styling

4. **Enhanced Metadata Display**
   - Agent avatars with color coding
   - Agent display names (full names instead of IDs)
   - Formatted date ranges (start to end)
   - Turn count badges
   - Topic tags with agent color accents
   - Episode summary with better typography""",
            "metadata": {
                "timestamp": "2024-12-20T10:05:00Z",
                "agent_id": "elena"
            }
        },
        {
            "role": "user",
            "content": "Now let's work on the durable execution workflow. We have logic that allows Elena to delegate visual creation and story creation two sage through temporal. We need to have some visibility and observability into that in the navigation UI the durable execution workflow page would be most appropriate for that.",
            "metadata": {
                "timestamp": "2024-12-20T11:00:00Z",
                "context": "Requesting workflow visibility for Elena → Sage delegations"
            }
        },
        {
            "role": "assistant",
            "content": """I've implemented comprehensive visibility and observability for durable execution workflows:

## Workflow Visibility Enhancements Complete

### Backend Enhancements

1. **Workflow Listing** (`backend/orchestration/workflow_service.py`)
   - Implemented Temporal visibility API integration
   - Added story workflow detection (workflow IDs starting with `story-`)
   - Automatic workflow type classification
   - Progress querying for story workflows

2. **Workflow API** (`backend/api/routers/workflows.py`)
   - Enhanced `/workflows` endpoint to include story workflows
   - Added story workflow progress support in `/workflows/{id}`
   - Step mapping for story workflows (5 steps: generating_story, generating_diagram, etc.)
   - Story preview in context snapshot

### Frontend Enhancements

1. **ActiveWorkflows Page**
   - Delegation chain visualization: shows Elena → Sage for story workflows
   - Agent avatars with color coding
   - Workflow type labels ("Story & Visual Creation")
   - Step information with formatted labels
   - Status badges with color coding
   - Error handling and loading states
   - Auto-refresh every 5 seconds

2. **WorkflowDetail Page**
   - Progress bar for story workflows (percentage complete)
   - Delegation chain visualization with agent avatars
   - Story preview display (first 200 chars)
   - Formatted step names (e.g., "Generating Story" instead of "generating_story")
   - Enhanced context snapshot handling
   - Workflow metadata display""",
            "metadata": {
                "timestamp": "2024-12-20T11:15:00Z",
                "agent_id": "elena"
            }
        },
        {
            "role": "user",
            "content": "Take the work we did on the episodes and ingested into ZEP as an episode and then also the work that we just did on the workflows, but I'm not quite clear of whether it would be considered a session or an episode. We need some clarity on what those two things do sessions and episodes.",
            "metadata": {
                "timestamp": "2024-12-20T12:00:00Z",
                "context": "Requesting clarification on Sessions vs Episodes"
            }
        },
        {
            "role": "assistant",
            "content": """I've created a comprehensive document clarifying the distinction between Sessions, Episodes, and Workflows:

## Sessions vs Episodes vs Workflows - Clarification

### Key Distinctions

1. **Sessions (Zep's Primary Concept)**
   - Top-level container for a conversation thread
   - Created when a user starts a new chat
   - Contains all messages in that conversation
   - Agents see only the current session's history strictly
   - Zep indexes sessions for semantic search across all sessions

2. **Episodes (Two Meanings)**
   - **Zep's Internal Episodes**: Automatic sub-segments within a session (managed by Zep)
   - **Engram's UI "Episodes"**: Historical conversation sessions (terminology overlap)
   - The `/episodes` endpoint actually lists sessions
   - This is a UI/UX term, not a strict Zep concept

3. **Workflows (Temporal Durable Execution)**
   - Durable execution processes managed by Temporal
   - Independent of sessions/episodes
   - Can be associated with sessions but are separate entities
   - Types: Agent workflows, Story workflows, Conversation workflows

### Answer to Your Question

**For the workflow visibility work:**
- Workflows are **not** sessions or episodes
- They are independent execution processes
- Story workflows (Elena → Sage) execute independently
- They can optionally create/update sessions, but are not sessions themselves

**For the episodes feature:**
- Episodes (in the UI) are actually **sessions**
- They're historical conversation sessions with summaries and metadata
- Users can continue conversations using the session ID

I've created `docs/concept/sessions-vs-episodes.md` with comprehensive documentation.""",
            "metadata": {
                "timestamp": "2024-12-20T12:10:00Z",
                "agent_id": "elena"
            }
        },
        {
            "role": "user",
            "content": "Ingest the thread working on both episodes and work flows into ZEP so that we can work with the agents on it",
            "metadata": {
                "timestamp": "2024-12-20T12:15:00Z",
                "context": "Requesting ingestion of this conversation into Zep"
            }
        }
    ]
    
    print(f"📝 Ingesting conversation into Zep...")
    print(f"   Session ID: {session_id}")
    print(f"   Messages: {len(messages)}")
    print(f"   Topics: {', '.join(topics)}")
    print()
    
    try:
        # Create or get session
        await client.get_or_create_session(
            session_id=session_id,
            user_id="user-derek",  # Default user for project history
            metadata={
                "summary": summary,
                "topics": topics,
                "agent_id": "elena",
                "turn_count": len(messages),
                "source": "conversation_ingestion",
                "created_at": "2024-12-20T10:00:00Z",
            }
        )
        
        print(f"✅ Session created/retrieved: {session_id}")
        
        # Add messages to session
        await client.add_memory(
            session_id=session_id,
            messages=messages,
        )
        
        print(f"✅ Added {len(messages)} messages to session")
        print()
        print(f"🎉 Conversation ingested successfully!")
        print(f"   Session ID: {session_id}")
        print(f"   Agents can now reference this conversation when discussing:")
        print(f"   - Episodes feature development")
        print(f"   - Workflow visibility enhancements")
        print(f"   - Sessions vs Episodes vs Workflows concepts")
        
    except Exception as e:
        print(f"❌ Error ingesting conversation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(ingest_conversation())

