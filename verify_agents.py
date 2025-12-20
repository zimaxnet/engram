from backend.agents.elena.agent import elena
from backend.agents.marcus.agent import marcus
import asyncio

print("Elena Tools:", [t.name for t in elena.tools])
print("Marcus Tools:", [t.name for t in marcus.tools])

assert "search_memory" in [t.name for t in elena.tools]
assert "search_memory" in [t.name for t in marcus.tools]
assert "check_workflow_status" in [t.name for t in marcus.tools]

print("✅ Agents Verified successfully")
