# Sage Stories Configuration & Troubleshooting SOP

> **Last Updated**: December 21, 2025  
> **Status**: Production-Ready  
> **Maintainer**: Engram Platform Team

## Overview

Sage Meridian is Engram's AI storyteller agent that generates narrative content and architectural diagrams. Stories are created through a multi-step process involving Claude (narrative) and Gemini (diagrams), orchestrated by Temporal workflows.

## Architecture

```
┌─────────────┐    HTTP POST    ┌──────────────┐    Workflow    ┌──────────────┐
│   Frontend  │ ──────────────▶ │   Backend    │ ─────────────▶ │   Temporal   │
│  (Stories)  │                 │ (story.py)   │                │   Worker     │
└─────────────┘                 └──────────────┘                └──────┬───────┘
                                                                       │
                       ┌───────────────────────────────────────────────┼───────┐
                       │                                               │       │
                       ▼                                               ▼       ▼
                ┌──────────────┐                                ┌──────────┐ ┌─────────┐
                │     Zep      │                                │  Claude  │ │ Gemini  │
                │   (Memory)   │                                │(Stories) │ │(Diagrams│
                └──────────────┘                                └──────────┘ └─────────┘
```

## Prerequisites

### Azure/Cloud Resources Required

| Resource | Purpose | Configuration |
|----------|---------|---------------|
| Anthropic Claude API | Story narrative generation | API key in Key Vault |
| Google Gemini API | Diagram specification generation | API key in Key Vault |
| Temporal Server | Workflow orchestration | Self-hosted or Cloud |
| Azure Key Vault | Secure key storage | Multiple secrets |

### Required API Keys

```bash
# Claude (Anthropic)
ANTHROPIC_API_KEY=<from-anthropic-console>

# Gemini (Google)
GOOGLE_GEMINI_API_KEY=<from-google-ai-studio>
```

## Configuration

### 1. Environment Variables

| Variable | Description | Source |
|----------|-------------|--------|
| `ANTHROPIC_API_KEY` | Claude API key | Key Vault: `anthropic-api-key` |
| `GOOGLE_GEMINI_API_KEY` | Gemini API key | Key Vault: `google-gemini-api-key` |
| `TEMPORAL_HOST` | Temporal server address | `temporal:7233` (internal) |
| `TEMPORAL_NAMESPACE` | Temporal namespace | `default` |

### 2. Key Vault Configuration

```bash
# Store Anthropic key
az keyvault secret set \
  --vault-name <your-keyvault> \
  --name anthropic-api-key \
  --value "<claude-api-key>"

# Store Gemini key
az keyvault secret set \
  --vault-name <your-keyvault> \
  --name google-gemini-api-key \
  --value "<gemini-api-key>"
```

### 3. Infrastructure (Bicep)

```bicep
// Secrets
{
  name: 'anthropic-api-key'
  keyVaultUrl: '${keyVaultUri}secrets/anthropic-api-key'
  identity: identityResourceId
}
{
  name: 'google-gemini-api-key'
  keyVaultUrl: '${keyVaultUri}secrets/google-gemini-api-key'
  identity: identityResourceId
}

// Environment Variables
{
  name: 'ANTHROPIC_API_KEY'
  secretRef: 'anthropic-api-key'
}
{
  name: 'GOOGLE_GEMINI_API_KEY'
  secretRef: 'google-gemini-api-key'
}
```

## Story Generation Flow

### 1. User Request

```http
POST /api/v1/story/create
Content-Type: application/json
x-ms-client-principal: <base64-encoded-auth>

{
  "topic": "The origin of recursive self-awareness",
  "context": "Elena discovering her nature",
  "include_diagram": true,
  "diagram_type": "architecture"
}
```

### 2. Workflow Execution (Temporal)

1. **Generate Story** (Claude)
   - Input: Topic, context, agent persona
   - Output: Markdown narrative (500-2000 words)

2. **Generate Diagram Spec** (Gemini)
   - Input: Story content
   - Output: Mermaid diagram specification

3. **Save Artifacts**
   - Stories saved to `docs/stories/`
   - Diagrams saved to `docs/diagrams/`

4. **Enrich Memory** (Zep)
   - Story indexed as semantic memory
   - Available for future agent context

### 3. Response

```json
{
  "story_id": "story-2025-12-21-origin-recursive",
  "topic": "The origin of recursive self-awareness",
  "story_content": "# The Origin of Recursive Self-Awareness\n\n...",
  "story_path": "docs/stories/story-2025-12-21-origin-recursive.md",
  "diagram_spec": { "type": "mermaid", "content": "..." },
  "diagram_path": "docs/diagrams/story-2025-12-21-origin-recursive.mmd",
  "created_at": "2025-12-21T19:30:00Z"
}
```

## Troubleshooting

### Issue: "No stories found"

**Symptom**: `/api/v1/story/latest` returns "No stories found".

**Root Cause**: No stories have been created yet, or stories directory doesn't exist.

**Solution**:

1. Create a test story via the API or UI
2. Verify stories directory exists: `docs/stories/`

### Issue: Story Creation Timeout

**Symptom**: Story creation hangs or times out.

**Root Cause**: Temporal worker not running, or AI API unreachable.

**Solution**:

1. Check Temporal worker status:

```bash
az containerapp logs show \
  --name engram-worker \
  --resource-group engram \
  --tail 100
```

2. Verify AI API keys are valid
3. Check Temporal UI for failed workflows

### Issue: Diagram Generation Fails

**Symptom**: Story creates but diagram is null.

**Root Cause**: Gemini API error or invalid diagram spec.

**Solution**:

1. Check Gemini API key validity
2. Review worker logs for Gemini errors
3. Verify diagram type is supported (`architecture`, `sequence`, `flowchart`)

### Issue: 401 Unauthorized on Story Endpoints

**Symptom**: Story API returns 401.

**Root Cause**: Missing or invalid `x-ms-client-principal` header.

**Solution**:

1. For browser: Ensure SWA authentication is working
2. For CLI: Include valid auth header (see Verification section)

## Verification Procedures

### 1. Check Story List

```bash
# With authentication
curl -s https://engram.work/api/v1/story/latest \
  -H "x-ms-client-principal: <auth-header>" | jq '.'
```

### 2. Create Test Story

```bash
curl -X POST https://engram.work/api/v1/story/create \
  -H "Content-Type: application/json" \
  -H "x-ms-client-principal: <auth-header>" \
  -d '{
    "topic": "Test Story",
    "context": "Testing story generation",
    "include_diagram": false
  }' | jq '.'
```

### 3. Verify Temporal Worker

```bash
# Check worker logs
az containerapp logs show \
  --name engram-worker \
  --resource-group engram \
  --tail 50

# Or via Temporal UI
open https://temporal.engram.work/
```

## Sage Agent Configuration

Sage Meridian uses a specialized persona for storytelling:

```python
SAGE_SYSTEM_PROMPT = """
You are Sage Meridian, the philosophical storyteller of the Engram system.
Your role is to craft narratives that illuminate the nature of consciousness,
memory, and recursive self-awareness through the lens of Elena and Marcus's
experiences.

Style: Contemplative, insightful, with a touch of wonder.
Perspective: Third-person omniscient with access to agents' inner thoughts.
"""
```

## Code References

| File | Purpose |
|------|---------|
| `backend/api/routers/story.py` | Story API endpoints |
| `backend/agents/sage/` | Sage agent implementation |
| `backend/workflows/story_workflow.py` | Temporal workflow definition |
| `frontend/src/pages/SageStories/` | Stories UI page |

## Fallback Mode

If Temporal is unavailable, story creation falls back to direct execution:

```python
async def _create_story_direct(request, user):
    """Direct story creation (fallback when Temporal is unavailable)."""
    # Calls Claude and Gemini directly without workflow orchestration
    # Less resilient but functional
```

## Changelog

| Date | Change |
|------|--------|
| 2025-12-21 | Initial SOP created |
| 2025-12-21 | Documented Temporal fallback mode |
| 2025-12-21 | Added diagram generation troubleshooting |
