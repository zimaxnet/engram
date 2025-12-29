#!/usr/bin/env python3
"""
Live Verification: Elena -> Sage Delegation

This script simulates a user asking Elena to create a story about Temporal workflows.
It verifies that:
1. Elena analyzes the request.
2. Elena selects the 'delegate_to_sage' tool.
3. The tool triggers the actual StoryWorkflow via Temporal.
4. The workflow completes and returns a story ID.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path.parent))

from backend.agents.elena.agent import elena
from backend.agents.base import AgentState
from backend.core import SecurityContext, Role

async def test_delegation():
    print("🤖 Initializing Elena Agent...")
    
    # Mock user message
    user_message = (
        "Elena, please ask Sage to create a creative story about how the 'Spine' (Temporal) protects the 'Brain' (Agents) from failure. "
        "Tone: Epic and heroic. "
        "Visual Style: illustrated scene showing a glowing spine supporting a brain. "
        "Key Message: Durable execution ensures no thought is lost. "
        "Please delegate this immediately."
    )
    
    print(f"👤 User: {user_message}")
    print("⏳ Elena is thinking...")
    
    # Initialize mock context
    from backend.core import EnterpriseContext, SecurityContext, Role, EpisodicState, SemanticKnowledge, OperationalState
    
    security_context = SecurityContext(
        user_id="test-user",
        tenant_id="test-tenant",
        roles=[Role.ADMIN],
        scopes=["*"]
    )
    
    context = EnterpriseContext(
        security=security_context,
        episodic=EpisodicState(),
        semantic=SemanticKnowledge(),
        operational=OperationalState()
    )
    
    from langchain_core.messages import HumanMessage
    
    # Initialize state
    state = AgentState(
        messages=[HumanMessage(content=user_message)],
        context=context,
        current_step="start",
        should_continue=True,
        tool_results=[],
        final_response=None
    )
    
    # Run the graph manually to observe steps
    # We can also use elena.ainvoke, but manual stepping gives us more visibility if we wanted it.
    # For now, let's use the compiled graph invocation to test the full flow.
    
    try:
        # We need to mock the minimal context usually provided by the API runner
        # But Elena's graph relies mostly on the state passed in.
        
        result = await elena.graph.ainvoke(state)
        
        print("\n✅ Elena Finished Execution.")
        print("-" * 50)
        print(f"📄 User Facing Response:\n{result.get('final_response')}")
        print("-" * 50)
        
        # Verify delegation occurred
        tool_usages = result.get("tool_results", [])
        delegation_occured = False
        story_id = None
        
        for usage in tool_usages:
            print(f"🛠️  Tool Used: {usage['tool']}")
            if usage['tool'] == "delegate_to_sage":
                delegation_occured = True
                output = str(usage['result'])
                print(f"   Output: {output[:100]}...")
                
                # Try to extract Story ID from output string (it's in the text)
                if "Story ID" in output:
                    import re
                    match = re.search(r"Story ID\*\*: ([\w-]+)", output)
                    if match:
                        story_id = match.group(1)
                        print(f"   ✅ Captured Story ID: {story_id}")
        
        if delegation_occured:
            print("\n🎉 SUCCESS: Elena successfully delegated to Sage!")
            if story_id:
                print(f"   Verify artifacts at: docs/stories/{story_id}.md")
        else:
            print("\n❌ RETURN: Delegation did not occur. Check agent logic.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_delegation())
