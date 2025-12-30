#!/usr/bin/env python3
"""
Interact with Marcus using backend code directly (bypasses API auth)

This script imports backend modules and calls Marcus directly.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Set environment to allow direct access
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("AUTH_REQUIRED", "false")  # Bypass auth for direct access

async def main():
    try:
        from backend.agents import get_agent
        from backend.core import EnterpriseContext, SecurityContext, Role
        
        print("🤖 Interacting with Marcus (Direct Backend)")
        print("=" * 60)
        
        # Create context
        security = SecurityContext(
            user_id="cli-user",
            tenant_id="cli-tenant", 
            roles=[Role.ADMIN],
            scopes=["*"],
            session_id="cli-marcus"
        )
        context = EnterpriseContext(security=security)
        context.episodic.conversation_id = "cli-marcus"
        
        # Get Marcus
        marcus = get_agent("marcus")
        print(f"✅ Loaded: {marcus.agent_name}\n")
        
        # Message
        message = """Marcus, I need you to create GitHub issues for the Enterprise Stability Improvement tasks.

Start with Phase 1 tasks (1.1, 1.2, 1.3, 1.4). Reference:
- Task list: scripts/create-stability-github-tasks.md  
- Stability analysis in Zep memory: enterprise-stability-analysis-2025-12-30

For each task, use create_github_issue with appropriate title, body, and labels."""
        
        print("💬 Sending message to Marcus...\n")
        response, ctx, agent_id = await marcus.run(message, context)
        
        print("=" * 60)
        print("✅ Marcus Response:")
        print("=" * 60)
        print(response)
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
