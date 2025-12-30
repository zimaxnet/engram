#!/usr/bin/env python3
"""
Ask Marcus to create GitHub issues for Enterprise Stability Improvements

This script sends a message to Marcus via the chat API to have him create
GitHub project tasks for the stability improvement plan.
"""

import asyncio
import httpx
import json
import sys
from datetime import datetime
from pathlib import Path

# Get API URL from environment or use default
API_URL = "https://staging-env-api.gentleriver-dd0de193.eastus2.azurecontainerapps.io"
SESSION_ID = f"stability-tasks-{int(datetime.now().timestamp())}"

# Read the task list to include in the message
TASK_LIST_PATH = Path(__file__).parent / "create-stability-github-tasks.md"

async def ask_marcus():
    """Send message to Marcus to create GitHub issues"""
    
    # Read task list if available
    task_list_context = ""
    if TASK_LIST_PATH.exists():
        with open(TASK_LIST_PATH, 'r', encoding='utf-8') as f:
            task_list_content = f.read()
            task_list_context = f"\n\nTask list is available in: scripts/create-stability-github-tasks.md\n\nHere's a summary:\n{task_list_content[:2000]}..."
    
    message = f"""Marcus, I need you to create GitHub issues for the Enterprise Stability Improvement tasks.

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

Please start by creating the Phase 1 tasks. After those are created, I'll ask you to create Phase 2-4 tasks.

{task_list_context}
"""
    
    print("🤖 Sending message to Marcus...")
    print(f"   API URL: {API_URL}")
    print(f"   Session ID: {SESSION_ID}")
    print(f"   Agent: marcus")
    print()
    print("📝 Message:")
    print("-" * 60)
    print(message[:500] + "..." if len(message) > 500 else message)
    print("-" * 60)
    print()
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            # Get auth token if needed (for enterprise auth)
            # For now, try without auth first (if AUTH_REQUIRED=false)
            headers = {
                "Content-Type": "application/json"
            }
            
            # Try to get token from environment or skip if auth is disabled
            # In enterprise mode, you'd need to get a token here
            
            response = await client.post(
                f"{API_URL}/api/v1/chat",
                json={
                    "content": message,
                    "agent_id": "marcus",
                    "session_id": SESSION_ID
                },
                headers=headers
            )
            
            print(f"📡 Response Status: {response.status_code}")
            print()
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Marcus Response:")
                print("=" * 60)
                print(data.get("content", ""))
                print("=" * 60)
                print()
                print(f"📊 Metadata:")
                print(f"   Agent: {data.get('agent_name', 'Unknown')}")
                print(f"   Message ID: {data.get('message_id', 'Unknown')}")
                print(f"   Session ID: {data.get('session_id', 'Unknown')}")
                if data.get('tokens_used'):
                    print(f"   Tokens Used: {data.get('tokens_used')}")
                if data.get('latency_ms'):
                    print(f"   Latency: {data.get('latency_ms'):.0f}ms")
                return True
            elif response.status_code == 401:
                print("❌ Authentication required")
                print("   Response:", response.text[:200])
                print()
                print("💡 Options:")
                print("   1. Set AUTH_REQUIRED=false in container app (for testing)")
                print("   2. Get auth token and include in Authorization header")
                print("   3. Use the frontend chat interface instead")
                return False
            else:
                print(f"❌ Request failed: {response.status_code}")
                print(f"   Response: {response.text[:500]}")
                return False
                
        except httpx.TimeoutException:
            print("❌ Request timed out (120s)")
            print("   Marcus may be processing a complex request")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """Main entry point"""
    print("🚀 Marcus Task Creation Request")
    print("=" * 60)
    print()
    
    success = await ask_marcus()
    
    print()
    print("=" * 60)
    if success:
        print("✅ Message sent to Marcus successfully!")
        print()
        print("📋 Next Steps:")
        print("   1. Check Marcus's response above")
        print("   2. Verify GitHub issues were created")
        print("   3. If Phase 1 tasks are created, ask Marcus to create Phase 2-4")
        print()
        print("💬 To continue the conversation, run this script again with:")
        print("   'Marcus, please create Phase 2 tasks (2.1, 2.2, 2.3)'")
    else:
        print("❌ Failed to send message to Marcus")
        print()
        print("💡 Alternative: Use the frontend chat interface to talk to Marcus")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))

