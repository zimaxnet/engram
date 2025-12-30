#!/usr/bin/env python3
"""
Interact with Marcus directly using backend code (bypasses API)

This script imports the backend agent code directly to interact with Marcus
without needing API authentication.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.agents import get_agent
from backend.core import EnterpriseContext, SecurityContext, Role
from backend.memory import enrich_context, persist_conversation


async def interact_with_marcus(message: str):
    """Interact with Marcus directly using backend code"""
    
    print("🤖 Interacting with Marcus (Direct Backend Access)")
    print("=" * 60)
    print()
    print(f"📝 Your message:")
    print(f"   {message}")
    print()
    
    try:
        # Create security context (POC user for direct access)
        security = SecurityContext(
            user_id="system-cli",
            tenant_id="system-tenant",
            roles=[Role.ADMIN],
            scopes=["*"],
            session_id="cli-session-marcus"
        )
        
        # Create enterprise context
        context = EnterpriseContext(security=security)
        context.episodic.conversation_id = "cli-session-marcus"
        
        # Get Marcus agent
        print("🔍 Loading Marcus agent...")
        marcus = get_agent("marcus")
        print(f"✅ Loaded: {marcus.agent_name}")
        print()
        
        # Enrich context with memory (optional, may timeout)
        print("🔍 Enriching context with memory...")
        try:
            context = await asyncio.wait_for(
                enrich_context(context, message),
                timeout=5.0
            )
            print("✅ Context enriched")
        except asyncio.TimeoutError:
            print("⚠️  Memory enrichment timed out (continuing anyway)")
        except Exception as e:
            print(f"⚠️  Memory enrichment failed: {e} (continuing anyway)")
        print()
        
        # Get response from Marcus
        print("💬 Getting response from Marcus...")
        print("-" * 60)
        
        response_text, updated_context, agent_id = await marcus.run(message, context)
        
        print()
        print("=" * 60)
        print("✅ Marcus Response:")
        print("=" * 60)
        print(response_text)
        print("=" * 60)
        print()
        
        # Persist conversation (fire-and-forget)
        try:
            await asyncio.wait_for(
                persist_conversation(updated_context),
                timeout=5.0
            )
            print("✅ Conversation persisted to memory")
        except Exception as e:
            print(f"⚠️  Failed to persist conversation: {e}")
        
        return response_text
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main entry point"""
    
    # Default message if not provided as argument
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
    else:
        message = """Marcus, I need you to create GitHub issues for the Enterprise Stability Improvement tasks.

**Context:**
- Stability analysis has been ingested into Zep memory (session: enterprise-stability-analysis-2025-12-30)
- We have a 4-phase improvement plan with 13 tasks
- Task structure is documented in: scripts/create-stability-github-tasks.md

**Your Task:**
Please create GitHub issues for all the stability improvement tasks. Start with Phase 1 tasks (1.1, 1.2, 1.3, 1.4) which are Critical/High priority.

**For each task, use create_github_issue with:**
- Title: Task number + name (e.g., "Task 1.1: Health Check Endpoints")
- Body: Description + acceptance criteria from the task list
- Labels: As specified (e.g., "stability", "phase-1", "health-checks", "backend")
- Project: Add to "Enterprise Stability Improvements" project (create if needed)

**Phase 1 Tasks to Create:**
1. Task 1.1: Health Check Endpoints (Critical, Backend)
2. Task 1.2: Configuration Validation on Startup (Critical, Backend)
3. Task 1.3: Graceful Degradation for Zep Memory (High, Memory)
4. Task 1.4: Error Tracking and Logging (High, Error Handling)

**Reference:**
- Search Zep memory for "enterprise stability analysis" or "stability improvement"
- Task details: scripts/create-stability-github-tasks.md
- Full analysis: docs/stability/enterprise-stability-analysis.md

Please start by creating the Phase 1 tasks. After those are created, I'll ask you to create Phase 2-4 tasks."""
    
    response = await interact_with_marcus(message)
    
    if response:
        print()
        print("✅ Interaction complete!")
        print()
        print("📋 Next Steps:")
        print("   1. Check Marcus's response above")
        print("   2. If he created issues, verify them in GitHub")
        print("   3. To continue, run this script again with a new message")
        print()
        print("💬 Example:")
        print("   python3 scripts/interact-with-marcus-direct.py 'Marcus, please create Phase 2 tasks now'")
        return 0
    else:
        print()
        print("❌ Interaction failed")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))

