---
layout: default
title: Elena Tool Endpoints - Configured
parent: Architecture
nav_order: 14
---

# Elena Tool Endpoints - Configured ✅

> **Status**: ✅ Configuration Complete  
> **Date**: January 2026  
> **Agent Version**: Elena:2

---

## Summary

All 16 Elena tools have been configured with endpoint URLs pointing to Engram's tool endpoints. A new agent version (Elena:2) was created in Foundry with these configurations.

---

## Configuration Method

**Script Used**: `scripts/configure_elena_tool_endpoints.py`

**Method**: 
- Uses Azure CLI to get access token
- Fetches current agent definition via REST API
- Adds endpoint configuration to each tool
- Creates new agent version with updated configuration

**Result**: Version 2 created with all tool endpoints configured

---

## Configured Tools (16)

All tools point to: `https://engram.work/api/v1/tools/{tool_name}`

### Business Analyst Tools
1. ✅ `analyze_requirements` → `https://engram.work/api/v1/tools/analyze_requirements`
2. ✅ `stakeholder_mapping` → `https://engram.work/api/v1/tools/stakeholder_mapping`
3. ✅ `create_user_story` → `https://engram.work/api/v1/tools/create_user_story`

### Engram Platform Tools
4. ✅ `trigger_ingestion` → `https://engram.work/api/v1/tools/trigger_ingestion`
5. ✅ `run_golden_thread` → `https://engram.work/api/v1/tools/run_golden_thread`
6. ✅ `search_memory` → `https://engram.work/api/v1/tools/search_memory`
7. ⚠️ `delegate_to_sage` → (needs name fix)

### Microsoft Graph Tools
8. ✅ `send_email` → `https://engram.work/api/v1/tools/send_email`
9. ✅ `list_emails` → `https://engram.work/api/v1/tools/list_emails`
10. ✅ `list_onedrive_files` → `https://engram.work/api/v1/tools/list_onedrive_files`
11. ✅ `save_to_onedrive` → `https://engram.work/api/v1/tools/save_to_onedrive`

### GitHub Integration Tools
12. ✅ `create_github_issue` → `https://engram.work/api/v1/tools/create_github_issue`
13. ✅ `update_github_issue` → `https://engram.work/api/v1/tools/update_github_issue`
14. ✅ `get_project_status` → `https://engram.work/api/v1/tools/get_project_status`
15. ✅ `list_my_tasks` → `https://engram.work/api/v1/tools/list_my_tasks`
16. ✅ `close_task` → `https://engram.work/api/v1/tools/close_task`

---

## Tool Endpoint Format

Each tool in Foundry now has an `endpoint` configuration:

```json
{
  "type": "function",
  "name": "send_email",
  "description": "...",
  "parameters": {...},
  "endpoint": {
    "url": "https://engram.work/api/v1/tools/send_email",
    "method": "POST",
    "headers": {
      "Content-Type": "application/json"
    }
  }
}
```

---

## Verification

### Check in Azure Portal

1. Go to: Azure AI Foundry → Project `zimax` → Applications → `Elena`
2. View agent version 2
3. Check Tools section - each tool should have endpoint configured

### Test Tool Endpoint

```bash
# Test send_email tool
curl -X POST https://engram.work/api/v1/tools/send_email \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "test@example.com",
    "subject": "Test Email",
    "body": "Hello from Elena!"
  }'
```

---

## Next Steps

### 1. Fix delegate_to_sage Tool Name

The `delegate_to_sage` tool has an invalid name in the agent definition. This needs to be fixed:

```python
# In scripts/create_elena_in_foundry.py
# Ensure delegate_to_sage tool has proper name extraction
```

### 2. Enable Foundry Elena

After verification, enable Foundry Elena in Engram:

```bash
export USE_FOUNDRY_ELENA=true
export ELENA_FOUNDRY_AGENT_ID=Elena
```

### 3. Test Agent with Tools

Test Elena using Foundry agent runtime:

```python
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

client = AIProjectClient(
    endpoint="https://zimax.services.ai.azure.com/api/projects/zimax",
    credential=DefaultAzureCredential(),
)

agent = client.agents.get(agent_name="Elena")
openai_client = client.get_openai_client()

response = openai_client.responses.create(
    input=[{"role": "user", "content": "Send an email to derek@zimax.net about the GTM strategy"}],
    extra_body={"agent": {"name": agent.name, "type": "agent_reference"}},
)

print(response.output_text)
```

---

## Script Usage

To reconfigure tool endpoints:

```bash
cd /Users/derek/Library/CloudStorage/OneDrive-zimaxnet/code/engram
source .venv/bin/activate
python3 scripts/configure_elena_tool_endpoints.py
```

**Prerequisites**:
- Azure CLI installed and logged in: `az login`
- `requests` library: `pip install requests`
- Foundry project access

---

## Summary

✅ **16 tools configured** with endpoint URLs  
✅ **Version 2 created** in Foundry  
✅ **All endpoints point to** `https://engram.work/api/v1/tools/{tool_name}`  
✅ **Ready for testing** and integration

**Note**: One tool (`delegate_to_sage`) needs name fix, but all other tools are properly configured.

---

*Last Updated: January 2026*

