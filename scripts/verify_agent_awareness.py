
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from backend.agents.elena.agent import elena
from backend.agents.marcus.agent import marcus
from backend.agents.sage.agent import sage

def verify_agent_awareness():
    print("🧪 Verifying Agent Tri-Search Awareness...\n")
    
    agents = [
        ("Elena (The Seller)", elena, ["Tri-Search", "Keyword Search", "Vector Search", "Knowledge Graph"]),
        ("Marcus (The Builder)", marcus, ["Tri-Search", "Deep Context Retrieval"]),
        ("Sage (The Storyteller)", sage, ["Tri-Search", "narrative threads"])
    ]
    
    all_passed = True
    
    for name, agent, keywords in agents:
        print(f"🔍 Checking {name} system prompt...")
        prompt = agent.system_prompt
        
        missing = []
        for kw in keywords:
            if kw not in prompt:
                missing.append(kw)
        
        if missing:
            print(f"❌ FAILED: {name} is missing keywords: {missing}")
            all_passed = False
        else:
            print(f"✅ PASSED: {name} is fully aware.")
            
    if all_passed:
        print("\n✨ All agents are Tri-Search aware!")
        sys.exit(0)
    else:
        print("\n⚠️  Some agents are missing context.")
        sys.exit(1)

if __name__ == "__main__":
    verify_agent_awareness()
