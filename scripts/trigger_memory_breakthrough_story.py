#!/usr/bin/env python3
"""
Trigger Sage to write a story about the Cross-Environment Memory Breakthrough.
"""

import asyncio
import os

# Override TEMPORAL_HOST for production connection
os.environ["TEMPORAL_HOST"] = "staging-env-temporal-server.gentleriver-dd0de193.eastus2.azurecontainerapps.io:443"

from backend.workflows.client import execute_story

async def main():
    topic = "The Vibe Coding Breakthrough: Cross-Environment Memory Query for AI Agents"
    context = """
    Today we achieved a significant breakthrough in AI-assisted development.
    
    THE DISCOVERY:
    While "vibe coding" with Antigravity, we noticed that past debugging sessions, 
    configuration changes, and architectural decisions were automatically surfacing 
    during the current session. This was "emergent contextual awareness" - the Memory 
    Graph was enriching the AI's understanding in real-time.
    
    THE BREAKTHROUGH:
    We realized the query_memory.py script that worked locally could also work with 
    Azure-deployed Zep. By adding a simple --env flag, AI agents in ANY IDE 
    (Antigravity, Cursor, VSCode) can now query the production Memory Graph:
    
    python -m backend.scripts.query_memory --env azure -q "voice live config"
    
    THE CONTINUOUS ENRICHMENT:
    We then implemented automatic memory enrichment:
    1. Git post-commit hooks auto-ingest commit context
    2. quick_ingest.py captures learnings instantly
    3. persist_conversation.py ingests Antigravity session artifacts
    
    THE IMPACT:
    This creates a "vibe coding" loop where development work automatically feeds 
    back into the Memory Graph. Every fix, every discovery, every architectural 
    decision becomes context for future AI sessions.
    
    AI agents can now ask: "What did I fix yesterday?" and get accurate answers.
    
    Please create a compelling story about this breakthrough with:
    - A diagram showing the memory enrichment flow
    - The significance for enterprise AI development
    - The "brain" metaphor of continuous learning
    """
    
    print(f"🧠 Triggering Sage workflow for: {topic}...")
    print(f"   Connecting to production Temporal: {os.environ['TEMPORAL_HOST']}")
    print("-" * 60)
    
    try:
        result = await execute_story(
            user_id="derek",
            tenant_id="default",
            topic=topic,
            context=context,
            include_diagram=True,
            include_image=True,
            diagram_type="flow"
        )
        
        if result.success:
            print(f"✅ SUCCESS: Story created with ID: {result.story_id}")
            print(f"\n📖 Story Preview:\n{result.story_content[:500]}...")
            if result.diagram:
                print(f"\n📊 Diagram included: Yes")
            if result.image_url:
                print(f"\n🖼️  Image: {result.image_url}")
        else:
            print(f"❌ FAILED: {result.error}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
