# MCP Tools User ID Attribution Test

**Document Version:** 1.0  
**Last Updated:** December 31, 2025  
**Status:** Test Documentation

---

## Overview

This document describes how to test that MCP tools properly receive and use `user_id` from agent context, ensuring proper user attribution for all operations.

---

## Test Requirements

1. **Backend Running**: API server must be running
2. **Zep Memory**: Zep memory service should be accessible (for memory operations)
3. **Test User ID**: Valid user ID to test with (e.g., from `token.oid`)

---

## Test Scenarios

### Test 1: MCP Tool with Explicit user_id

**Objective:** Verify that MCP tools accept `user_id` parameter and use it correctly.

**Tools to Test:**
- `chat_with_agent(user_id=...)`
- `enrich_memory(user_id=...)`
- `search_memory(user_id=...)`
- `ingest_document(user_id=...)`

**Steps:**
1. Call MCP tool with explicit `user_id` parameter
2. Verify tool uses provided `user_id`
3. Check backend logs for user_id in operations

**Expected Result:**
- Tool accepts `user_id` parameter
- Tool uses provided `user_id` (not fallback)
- Backend logs show operations with correct `user_id`
- No warning about missing `user_id`

**Test Script:**
```bash
python3 scripts/test-mcp-tools-user-id.py --user-id <USER_ID> --tool all
```

---

### Test 2: MCP Tool without user_id (Fallback)

**Objective:** Verify that MCP tools fall back to default user when `user_id` is not provided.

**Steps:**
1. Call MCP tool without `user_id` parameter
2. Verify tool uses fallback user
3. Check backend logs for warning message

**Expected Result:**
- Tool uses fallback `user_id="mcp-user"`
- Backend logs show warning: `"<tool_name> called without user_id - using fallback"`
- Operations still work but with fallback user

**Test Script:**
```python
# Manual test
from backend.api.routers.mcp_server import chat_with_agent

# Call without user_id
result = await chat_with_agent(
    message="Test",
    session_id="test-session"
)
# Should log warning about missing user_id
```

---

### Test 3: Agent Tool Invocation with Context

**Objective:** Verify that agents inject `user_id` from `EnterpriseContext` into tool arguments.

**Steps:**
1. Create `EnterpriseContext` with `SecurityContext` containing `user_id`
2. Agent calls MCP tool
3. Verify tool receives `user_id` from context

**Expected Result:**
- Agent extracts `user_id` from `context.security.user_id`
- Agent injects `user_id` into tool arguments
- Tool receives and uses correct `user_id`
- No fallback warning in logs

**Test Code:**
```python
from backend.core import EnterpriseContext, SecurityContext, Role
from backend.agents.marcus.agent import MarcusAgent

# Create context with user_id
security = SecurityContext(
    user_id="test-user-123",
    tenant_id="test-tenant",
    roles=[Role.ANALYST],
    scopes=["*"]
)
context = EnterpriseContext(security=security)

# Agent should inject user_id when calling tools
agent = MarcusAgent()
# When agent calls tools, user_id should be injected
```

---

### Test 4: Tool Schema Inspection

**Objective:** Verify that agents can detect which tools accept `user_id` parameter.

**Steps:**
1. Inspect tool schema for `user_id` field
2. Verify agent can detect this field
3. Verify agent injects `user_id` only for tools that accept it

**Expected Result:**
- Agent can inspect tool `args_schema.model_fields` or `__fields__`
- Agent detects `user_id` field in tool schema
- Agent injects `user_id` only when field exists

---

## Automated Testing

### Using Test Script

```bash
# Test all tools with specific user_id
python3 scripts/test-mcp-tools-user-id.py --user-id d240186f-f80e-4369-9296-57fef571cd93

# Test specific tool
python3 scripts/test-mcp-tools-user-id.py --user-id <USER_ID> --tool chat

# Test agent tool invocation
python3 scripts/test-mcp-tools-user-id.py --user-id <USER_ID> --tool agent
```

### Expected Output

```
============================================================
MCP Tools User ID Attribution Test
============================================================
User ID: test-user-123
Tool: all

Test 1: chat_with_agent
------------------------------------------------------------
Testing chat_with_agent with user_id: test-user-123
✅ chat_with_agent result: Hello! I'm Dr. Elena Vasquez...

Test 2: enrich_memory
------------------------------------------------------------
Testing enrich_memory with user_id: test-user-123
✅ enrich_memory result: Memory enriched successfully.

...

============================================================
Test Summary
============================================================
✅ chat: PASSED
✅ enrich: PASSED
✅ search: PASSED
✅ ingest: PASSED
✅ agent: PASSED

✅ All tests passed!
```

---

## Backend Log Verification

Check backend logs for user_id usage:

**Success (with user_id):**
```
INFO: chat_with_agent called with user_id: test-user-123
INFO: Created Zep session with user_id: test-user-123
```

**Warning (without user_id):**
```
WARNING: chat_with_agent called without user_id - using fallback
INFO: Created Zep session with user_id: mcp-user
```

**Agent Injection:**
```
DEBUG: Injected user_id=test-user-123 into tool chat_with_agent
```

---

## Manual Testing

### Test via Agent Chat

1. Send chat message through API with authenticated user
2. Agent should call MCP tools with user_id from context
3. Check logs for user_id injection

```bash
# Send chat message
curl -X POST https://api.engram.work/api/v1/chat \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Search memory for test",
    "agent_id": "elena",
    "session_id": "test-session"
  }'

# Check logs for:
# - Agent tool invocation
# - user_id injection
# - MCP tool execution with user_id
```

---

## Troubleshooting

### Issue: Tool uses fallback user_id

**Possible Causes:**
- Agent not injecting user_id
- Tool not receiving user_id parameter
- Context not properly set up

**Solutions:**
- Verify `EnterpriseContext.security.user_id` is set
- Check agent `_maybe_use_tool` method
- Verify tool schema includes `user_id` field
- Check backend logs for injection messages

### Issue: Tool fails with user_id parameter

**Possible Causes:**
- Tool signature doesn't match
- Parameter type mismatch
- Tool implementation error

**Solutions:**
- Verify tool signature includes `user_id: Optional[str] = None`
- Check tool implementation uses `actual_user_id = user_id or "mcp-user"`
- Review tool code for errors

---

## Related Documentation

- `docs/architecture/user-identity-flow-comprehensive.md` - Complete user identity flow
- `docs/architecture/user-identity-fixes-required.md` - Implementation details
- `backend/api/routers/mcp_server.py` - MCP tool implementations
- `backend/agents/base.py` - Agent base class

