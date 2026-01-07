---
layout: default
title: Azure AI Foundry Integration
parent: Features
nav_order: 10
---

# Azure AI Foundry Integration

> **Status**: ✅ Production Ready  
> **Last Updated**: January 2026  
> **Feature**: Enterprise AI Agent Platform Integration

---

## Overview

Engram integrates with **Azure AI Foundry Agent Service** to provide enterprise-grade agent capabilities, including:

- **Thread Management**: Persistent conversation threads across sessions
- **Agent Runtime**: Native Foundry agent execution with full tool support
- **Avatar Support**: Photorealistic video avatars for agents
- **Enterprise Search**: Foundry IQ for document grounding
- **Tool Integration**: Seamless Microsoft Graph and Engram tool execution

---

## Key Features

### 1. **Agent Thread Management** 🧵

**What It Does**:
- Creates persistent conversation threads in Foundry
- Maintains conversation history across sessions
- Enables multi-turn conversations with context

**How It Works**:
- Each user-agent conversation gets a unique Foundry thread
- Threads are scoped by user, agent, and project
- Thread metadata includes session IDs and timestamps

**Configuration**:
```bash
# Enable Foundry thread management
USE_FOUNDRY_THREADS=true
```

---

### 2. **Elena Foundry Agent** 👩‍💼

**What It Does**:
- Runs Elena as a native Foundry agent
- Maintains all Microsoft Graph capabilities (email, OneDrive)
- Provides photorealistic avatar support

**How It Works**:
- Elena's agent definition is stored in Foundry
- Engram tools are exposed as HTTP endpoints
- Foundry calls Engram tools when needed
- Avatar videos are generated automatically

**Configuration**:
```bash
# Enable Foundry Elena
USE_FOUNDRY_ELENA=true
ELENA_FOUNDRY_AGENT_ID=Elena
```

**See Also**: [Elena Avatar Configuration](../architecture/elena-avatar-configuration.md)

---

### 3. **Foundry IQ Enterprise Search** 🔍

**What It Does**:
- Integrates Azure AI Search knowledge bases
- Provides enterprise document grounding
- Combines with Engram's tri-search (keyword, vector, graph)

**How It Works**:
- Foundry IQ searches knowledge bases
- Results are fused with Engram search results using RRF
- Provides comprehensive enterprise knowledge access

**Configuration**:
```bash
# Enable Foundry IQ
USE_FOUNDRY_IQ=true
FOUNDRY_IQ_KB_ID=<knowledge-base-id>
```

**See Also**: [Foundry IQ Integration](../architecture/foundry-iq-integration-summary.md)

---

## Configuration

### Required Secrets (Key Vault)

All Foundry configuration is stored in **Azure Key Vault** (production source of truth):

| Secret Name | Description | Example |
|------------|-------------|---------|
| `azure-foundry-agent-endpoint` | Foundry API endpoint | `https://zimax.services.ai.azure.com` |
| `azure-foundry-agent-project` | Foundry project name | `zimax` |
| `azure-foundry-agent-key` | Optional API key (uses Managed Identity if not set) | `<api-key>` |
| `elena-foundry-agent-id` | Elena's agent ID in Foundry | `Elena` |

### Environment Variables

The Container App automatically loads secrets from Key Vault:

```bash
AZURE_FOUNDRY_AGENT_ENDPOINT=<from-key-vault>
AZURE_FOUNDRY_AGENT_PROJECT=<from-key-vault>
AZURE_FOUNDRY_AGENT_KEY=<from-key-vault>
AZURE_FOUNDRY_AGENT_API_VERSION=2025-11-15-preview
ELENA_FOUNDRY_AGENT_ID=<from-key-vault>
```

### Feature Flags

Enable Foundry features via environment variables:

```bash
# Thread management
USE_FOUNDRY_THREADS=true

# Elena as Foundry agent
USE_FOUNDRY_ELENA=true

# Enterprise search
USE_FOUNDRY_IQ=true
FOUNDRY_IQ_KB_ID=<kb-id>
```

**Default**: All flags are `false` (zero production impact)

---

## Architecture

### Integration Pattern

```
┌─────────────┐
│   Engram    │
│  Frontend   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Engram API │
│  (FastAPI)  │
└──────┬──────┘
       │
       ├─────────────────┐
       │                 │
       ▼                 ▼
┌─────────────┐   ┌─────────────┐
│   Foundry   │   │  Engram     │
│   Agent     │◄──┤  Tools API  │
│   Service   │   │  (HTTP)     │
└─────────────┘   └─────────────┘
       │
       ▼
┌─────────────┐
│  Microsoft  │
│    Graph    │
└─────────────┘
```

### How It Works

1. **User sends message** → Engram API
2. **Engram routes to Foundry** (if `USE_FOUNDRY_ELENA=true`)
3. **Foundry executes agent** with tools
4. **Tools call Engram API** endpoints
5. **Foundry returns response** with avatar video URL
6. **Engram displays** response and avatar

---

## Setup Instructions

### 1. Configure Key Vault Secrets

```bash
# Set Foundry endpoint
az keyvault secret set \
  --vault-name "<key-vault-name>" \
  --name "azure-foundry-agent-endpoint" \
  --value "https://zimax.services.ai.azure.com"

# Set Foundry project
az keyvault secret set \
  --vault-name "<key-vault-name>" \
  --name "azure-foundry-agent-project" \
  --value "zimax"

# Set Elena agent ID
az keyvault secret set \
  --vault-name "<key-vault-name>" \
  --name "elena-foundry-agent-id" \
  --value "Elena"
```

### 2. Create Elena in Foundry

```bash
# Run migration script
python3 scripts/create_elena_in_foundry.py
```

**See Also**: [Elena Foundry Migration](../architecture/elena-foundry-migration-complete.md)

### 3. Configure Tool Endpoints

```bash
# Configure all 16 tool endpoints
python3 scripts/configure_elena_tool_endpoints.py
```

### 4. Configure Avatar

```bash
# Enable avatar for Elena
python3 scripts/configure_elena_avatar.py
```

### 5. Enable Feature Flags

Set in Container App environment variables or GitHub Secrets:

```bash
USE_FOUNDRY_ELENA=true
USE_FOUNDRY_THREADS=true  # Optional
USE_FOUNDRY_IQ=true        # Optional
```

---

## Benefits

### ✅ Enterprise Grade
- Managed agent runtime
- Built-in observability
- Scalable infrastructure

### ✅ Seamless Integration
- Zero impact on existing features
- Feature flags for gradual rollout
- Graceful fallback to LangGraph

### ✅ Enhanced Capabilities
- Photorealistic avatars
- Enterprise document search
- Persistent conversation threads

### ✅ Security
- Managed Identity authentication
- Key Vault secret management
- RBAC access control

---

## Troubleshooting

### Avatar Not Showing

**Check**:
1. `USE_FOUNDRY_ELENA=true` is set
2. `ELENA_FOUNDRY_AGENT_ID` is correct
3. Elena agent has avatar configured in Foundry
4. Container App has access to Key Vault secrets

**Debug**:
```bash
# Check environment variables
az containerapp exec --name <app-name> --resource-group <rg> --command "env | grep FOUNDRY"

# Check logs
az containerapp logs show --name <app-name> --resource-group <rg> --tail 50
```

### Tools Not Working

**Check**:
1. Tool endpoints are configured in Foundry
2. Engram API is accessible from Foundry
3. Tool endpoint URLs are correct

**Debug**:
```bash
# Test tool endpoint
curl -X POST https://engram.work/api/v1/tools/send_email \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"to": "test@example.com", "subject": "Test", "body": "Test"}'
```

### Thread Management Issues

**Check**:
1. `USE_FOUNDRY_THREADS=true` is set
2. Foundry endpoint and project are configured
3. Managed Identity has access to Foundry

**Debug**:
```bash
# Check Foundry client initialization
az containerapp logs show --name <app-name> --resource-group <rg> --tail 100 | grep -i foundry
```

---

## Related Documentation

- [Foundry Configuration Setup](../architecture/foundry-configuration-setup.md)
- [Elena Avatar Configuration](../architecture/elena-avatar-configuration.md)
- [Foundry IQ Integration](../architecture/foundry-iq-integration-summary.md)
- [Agent User Isolation](../architecture/agent-user-isolation.md)
- [Configuration Source of Truth](../architecture/configuration-source-of-truth.md)

---

## Next Steps

1. ✅ **Configure Foundry secrets** in Key Vault
2. ✅ **Create Elena agent** in Foundry
3. ✅ **Configure tool endpoints** for Microsoft Graph
4. ✅ **Enable avatar** for Elena
5. ✅ **Set feature flags** to enable Foundry features
6. 🔄 **Test avatar** in chat interface
7. 🔄 **Enable Foundry IQ** for enterprise search (optional)

---

## Support

For issues or questions:
- Check [Troubleshooting](#troubleshooting) section
- Review [Architecture Documentation](../architecture/)
- Check application logs: `az containerapp logs show`

