---
layout: default
title: Elena Foundry Migration - Complete
parent: Architecture
nav_order: 13
---

# Elena Foundry Migration - Complete ✅

> **Status**: ✅ Migration Complete  
> **Date**: January 2026  
> **Agent ID**: `Elena`

---

## Migration Summary

Elena has been successfully created in Azure AI Foundry as a hosted agent with all her Microsoft Graph capabilities.

### ✅ What Was Completed

1. **Agent Created in Foundry**
   - Agent Name: `Elena`
   - Agent ID: `Elena`
   - Kind: `prompt` (simple agent with instructions/model/tools)
   - Tools: 16 tools converted and registered
   - System Prompt: 4,577 characters

2. **Configuration Updated**
   - API Version: `2025-11-15-preview` (correct version)
   - Endpoint: `https://zimax.services.ai.azure.com/api/projects/zimax`
   - Authentication: Managed Identity (working)

3. **Tool Conversion**
   - All 16 Elena tools converted to Foundry format
   - Tools include: Microsoft Graph (email, OneDrive), memory search, BA tools, GitHub integration

---

## Correct API Configuration

### API Version
```bash
AZURE_FOUNDRY_AGENT_API_VERSION="2025-11-15-preview"
```

### Endpoint Structure
```
https://zimax.services.ai.azure.com/api/projects/zimax
```

### Agent Creation Payload Format

```json
{
  "name": "Elena",
  "definition": {
    "kind": "prompt",
    "instructions": "...",
    "model": "gpt-5.2-chat",
    "tools": [
      {
        "type": "function",
        "name": "send_email",
        "description": "...",
        "parameters": {...}
      }
    ],
    "temperature": 0.7
  }
}
```

**Key Points**:
- ✅ `name` at root level
- ✅ `definition` object with `kind: "prompt"`
- ✅ Tools with `type: "function"` at root level (not nested)
- ✅ API version: `2025-11-15-preview`

---

## Next Steps

### 1. Configure Tool Endpoints in Foundry

Elena's tools need to be configured in Foundry to point to Engram's tool endpoints:

1. Go to Azure Portal → Azure AI Foundry → Project `zimax` → Applications → `Elena`
2. Edit agent configuration
3. For each tool, configure the endpoint:
   - **Endpoint URL**: `https://engram.work/api/v1/tools/{tool_name}`
   - **Method**: `POST`
   - **Headers**: `Authorization: Bearer <token>`

**Tools to Configure**:
- `send_email` → `https://engram.work/api/v1/tools/send_email`
- `list_emails` → `https://engram.work/api/v1/tools/list_emails`
- `list_onedrive_files` → `https://engram.work/api/v1/tools/list_onedrive_files`
- `save_to_onedrive` → `https://engram.work/api/v1/tools/save_to_onedrive`
- `search_memory` → `https://engram.work/api/v1/tools/search_memory`
- ... (all 16 tools)

### 2. Store Agent ID in Key Vault

```bash
az keyvault secret set \
  --vault-name "staging-env-kv" \
  --name "elena-foundry-agent-id" \
  --value "Elena"
```

### 3. Add to GitHub Secrets

- `ELENA_FOUNDRY_AGENT_ID` → `Elena`

### 4. Enable Foundry Elena

After deployment, set environment variable:
```bash
export USE_FOUNDRY_ELENA=true
export ELENA_FOUNDRY_AGENT_ID=Elena
```

---

## Agent Details

### Agent ID
```
Elena
```

### Tools Registered (16)
1. `analyze_requirements`
2. `stakeholder_mapping`
3. `create_user_story`
4. `trigger_ingestion`
5. `run_golden_thread`
6. `search_memory`
7. `delegate_to_sage`
8. `send_email`
9. `list_emails`
10. `list_onedrive_files`
11. `save_to_onedrive`
12. `create_github_issue`
13. `update_github_issue`
14. `get_project_status`
15. `list_my_tasks`
16. `close_task`

### System Prompt
- Length: 4,577 characters
- Includes: Elena's persona, expertise, communication style, Microsoft Graph capabilities

---

## Testing

### Test Agent Creation

```bash
cd /Users/derek/Library/CloudStorage/OneDrive-zimaxnet/code/engram
source .venv/bin/activate
export AZURE_FOUNDRY_AGENT_ENDPOINT="https://zimax.services.ai.azure.com"
export AZURE_FOUNDRY_AGENT_PROJECT="zimax"
export AZURE_FOUNDRY_AGENT_API_VERSION="2025-11-15-preview"
python3 scripts/create_elena_in_foundry.py
```

### Verify Agent in Foundry

```python
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

client = AIProjectClient(
    endpoint="https://zimax.services.ai.azure.com/api/projects/zimax",
    credential=DefaultAzureCredential(),
)

agent = client.agents.get(agent_name="Elena")
print(f"Agent: {agent.name}, ID: {agent.id}")
```

---

## Troubleshooting

### Issue: "API version not supported"
**Solution**: Use `2025-11-15-preview` (not `2024-10-01-preview`)

### Issue: "Required properties [\"definition\"] are not present"
**Solution**: Use payload structure with `name` at root and `definition` object

### Issue: "Must be one of: [prompt, hosted, container_app, workflow]"
**Solution**: Use `kind: "prompt"` for simple agents (not `"agent"` or `"hosted"`)

### Issue: "Required properties [\"type\"] are not present" (tools)
**Solution**: Tools need `type: "function"` at root level, not nested

---

## Summary

✅ **Elena successfully created in Foundry**
- Agent ID: `Elena`
- 16 tools registered
- Ready for tool endpoint configuration
- Ready for integration with Engram

**Next**: Configure tool endpoints in Foundry portal, then enable `USE_FOUNDRY_ELENA` feature flag.

---

*Last Updated: January 2026*

