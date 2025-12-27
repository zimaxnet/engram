#!/usr/bin/env python3
"""
Create a story about GitHub Projects integration via Sage's delegation

This script delegates to Sage to create a story and visual about the GitHub Projects
integration for tracking the Production-Grade Agentic System implementation.
"""

import asyncio
import sys
from pathlib import Path
import os

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set environment variables if needed
os.environ.setdefault("ENVIRONMENT", "development")

async def delegate_to_sage():
    """Delegate story creation to Sage"""
    
    # Import here to avoid issues if dependencies aren't available
    try:
        from backend.workflows.client import execute_story
    except ImportError as e:
        print(f"❌ Cannot import workflow client: {e}")
        print("   This script requires Temporal and backend dependencies.")
        print("   Run from backend environment or use API endpoint instead.")
        return None
    
    topic = "GitHub Projects Integration for Engram Context Engine"
    context = """
    The Engram Context Engine has integrated GitHub Projects to enable comprehensive tracking 
    of the Production-Grade Agentic System implementation across all seven layers. This integration 
    allows Elena (Business Analyst) and Marcus (Project Manager) agents to actively manage tasks, 
    track progress, and maintain visibility. The story should cover:
    
    1. How GitHub Projects applies to each of the seven layers of agentic AI systems
    2. The progress tracking mechanism and task lifecycle
    3. Agent capabilities and workflows (Elena, Marcus, Sage)
    4. System awareness of progress through recursive self-awareness
    5. Benefits for agents, system, and users
    
    The story should be engaging, technical but accessible, and highlight the recursive self-awareness 
    of the agents tracking their own work. Include metaphors and visual descriptions.
    """
    
    print("📖 Delegating to Sage to create story about GitHub Projects integration...")
    print(f"   Topic: {topic}")
    print()
    
    try:
        result = await execute_story(
            user_id="system-delegate",
            tenant_id="default",
            topic=topic,
            context=context,
            include_diagram=True,
            include_image=True,
            diagram_type="architecture"
        )
        
        if result.success:
            print("✅ Story created successfully!")
            print(f"   Story ID: {result.story_id}")
            print(f"   Story Path: {result.story_path}")
            print(f"   Diagram Path: {result.diagram_path}")
            print(f"   Image Path: {result.image_path}")
            print(f"   Memory Session ID: {result.memory_session_id}")
            print(f"\n   Preview: {result.story_content[:300]}...")
            print(f"\n📝 Story and visual have been:")
            print(f"   ✅ Saved to docs folder (OneDrive sync)")
            print(f"   ✅ Ingested into Zep memory (session: {result.memory_session_id})")
            return result.story_id
        else:
            print(f"❌ Failed to create story: {result.error}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating story: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    story_id = asyncio.run(delegate_to_sage())
    if story_id:
        print(f"\n🎉 Story creation complete!")
        print(f"   Story ID: {story_id}")
        print(f"   View at: /stories/{story_id}")
    else:
        print("\n⚠️  Story creation failed. Check Temporal worker is running.")

