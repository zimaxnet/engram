#!/usr/bin/env python3
"""
Ingest GPT-5.1-chat API Parameters Fix Episode

Documents the resolution of chat endpoint failures caused by incorrect
API parameters for the gpt-5.1-chat model.
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path.parent))

from backend.memory.client import ZepMemoryClient

ZEP_URL = os.getenv("ZEP_API_URL", "https://staging-env-zep.gentleriver-dd0de193.eastus2.azurecontainerapps.io")
SESSION_ID = "capability-gpt-5.1-chat-api-parameters-fix-2025-12-31"
USER_ID = "system"

# Set ZEP_API_URL if provided
if ZEP_URL:
    os.environ["ZEP_API_URL"] = ZEP_URL

METADATA = {
    "type": "capability",
    "category": "troubleshooting",
    "title": "GPT-5.1-chat API Parameters Fix",
    "summary": "Resolved chat endpoint failures by updating API parameters for gpt-5.1-chat model. Changed max_tokens to max_completion_tokens and removed temperature parameter support for this model.",
    "topics": [
        "gpt-5.1-chat",
        "api-parameters",
        "max_completion_tokens",
        "temperature",
        "azure-ai-foundry",
        "chat-endpoint",
        "llm-api",
        "troubleshooting",
        "model-compatibility",
        "api-version",
        "2024-12-01-preview",
    ],
    "date": "2025-12-31",
    "status": "resolved",
    "component": "backend/agents/base.py",
    "severity": "high",
    "impact": "Chat endpoint completely non-functional",
}

MESSAGES = [
    {
        "role": "user",
        "content": "Chat endpoint is returning error messages instead of agent responses. Users can authenticate successfully, but chat interactions fail with generic error messages.",
        "metadata": {"agent_id": "system"}
    },
    {
        "role": "assistant",
        "content": "Let me investigate the chat endpoint issue. I'll test the endpoint directly to see what's happening.",
        "metadata": {"agent_id": "elena"}
    },
    {
        "role": "user",
        "content": "The endpoint returns HTTP 200, but the response content is an error message. Also, tokens_used is 0, which suggests the LLM call is failing.",
        "metadata": {"agent_id": "system"}
    },
    {
        "role": "assistant",
        "content": "I've confirmed the issue: authentication is working, but agent execution is failing. The tokens_used: 0 indicates the LLM API call is not succeeding. Let me check the backend logs and test the Azure AI Foundry endpoint directly.",
        "metadata": {"agent_id": "elena"}
    },
    {
        "role": "user",
        "content": "Here's the endpoint URL and API key: https://zimax-gw.azure-api.net/zimax/openai/deployments/gpt-5.1-chat/chat/completions?api-version=2024-05-01-preview",
        "metadata": {"agent_id": "system"}
    },
    {
        "role": "assistant",
        "content": """I've tested the endpoint and found the root cause. The gpt-5.1-chat model requires different API parameters than older models:

1. **max_tokens → max_completion_tokens**: The model requires `max_completion_tokens` instead of `max_tokens`
2. **Temperature not supported**: The model only supports the default temperature value (1), custom values like 0.7 are not allowed
3. **API version**: Requires `2024-12-01-preview` or later (not `2024-05-01-preview`)

The backend code was sending `max_tokens` and `temperature` parameters, which caused the API to return 400 Bad Request errors.

Error messages from API:
- "Unsupported parameter: 'max_tokens' is not supported with this model. Use 'max_completion_tokens' instead."
- "Unsupported value: 'temperature' does not support 0.7 with this model. Only the default (1) value is supported."""",
        "metadata": {"agent_id": "elena"}
    },
    {
        "role": "user",
        "content": "Perfect! Please fix the code to handle gpt-5.1-chat model requirements correctly.",
        "metadata": {"agent_id": "system"}
    },
    {
        "role": "assistant",
        "content": """I've implemented the fix in `backend/agents/base.py`:

**Changes Made:**

1. **Store deployment name** for model-specific handling:
   ```python
   self.deployment = deployment
   ```

2. **Use max_completion_tokens** for Azure format endpoints:
   ```python
   payload["max_completion_tokens"] = self.max_tokens
   ```

3. **Skip temperature parameter** for gpt-5.1-chat models:
   ```python
   if self.deployment and "gpt-5.1" not in self.deployment.lower():
       payload["temperature"] = self.temperature
   ```

This ensures backward compatibility with older models (gpt-4, gpt-35-turbo) while correctly handling gpt-5.1-chat requirements.

**Testing Confirmed:**
- ✅ Works with max_completion_tokens
- ✅ Works without temperature parameter
- ✅ Requires API version 2024-12-01-preview

The fix has been committed and pushed. Once deployment completes, the chat endpoint should work correctly.""",
        "metadata": {"agent_id": "elena"}
    },
    {
        "role": "user",
        "content": "Great work! Please document this fix and ensure it's available in memory for future troubleshooting.",
        "metadata": {"agent_id": "system"}
    },
    {
        "role": "assistant",
        "content": """I've created comprehensive documentation:

1. **Troubleshooting Guide**: `docs/troubleshooting/gpt-5.1-chat-api-parameters-fix.md`
   - Complete problem statement
   - Root cause analysis
   - Solution details
   - Testing procedures
   - Model compatibility matrix

2. **Test Script**: `scripts/test-azure-foundry-direct.py`
   - Tests both API versions
   - Tests both endpoint formats
   - Helps diagnose configuration issues

3. **Memory Ingestion**: This episode is being ingested into Zep memory so agents can reference it when:
   - Troubleshooting chat endpoint failures
   - Configuring new models
   - Understanding model-specific API requirements
   - Planning model upgrades

The documentation includes a model compatibility table showing which models support which parameters, which will be helpful for future model integrations.""",
        "metadata": {"agent_id": "elena"}
    }
]

# Add full documentation content as a system message
DOC_CONTENT = """
# GPT-5.1-chat API Parameters Fix

**Date:** December 31, 2025  
**Issue:** Chat endpoint failing with LLM API errors  
**Root Cause:** `gpt-5.1-chat` model has different API parameter requirements

## Problem

Chat endpoint was returning error messages because the LLM API calls were failing with:
- `400 Bad Request: Unsupported parameter: 'max_tokens' is not supported with this model. Use 'max_completion_tokens' instead.`
- `400 Bad Request: Unsupported value: 'temperature' does not support 0.7 with this model. Only the default (1) value is supported.`

## Root Cause

The `gpt-5.1-chat` model (version `2025-11-13`) has different API parameter requirements than older models:

1. **`max_tokens` → `max_completion_tokens`**: The model requires `max_completion_tokens` instead of `max_tokens`
2. **Temperature not supported**: The model only supports the default temperature value (1), custom values like 0.7 are not allowed
3. **API version**: Requires `2024-12-01-preview` or later (not `2024-05-01-preview`)

## Solution

Updated `backend/agents/base.py` `FoundryChatClient` class to:

1. **Use `max_completion_tokens` for Azure format endpoints** (instead of `max_tokens`)
2. **Skip `temperature` parameter for `gpt-5.1-chat` models** (only send for older models)
3. **Store deployment name** to enable model-specific handling

### Code Implementation

```python
# Store deployment name for model-specific handling
self.deployment = deployment

# In ainvoke method:
if not self.is_openai_compat:
    # gpt-5.1-chat doesn't support custom temperature, so don't send it
    # For older models, temperature is supported
    if self.deployment and "gpt-5.1" not in self.deployment.lower():
        payload["temperature"] = self.temperature
    # Use max_completion_tokens for newer models (gpt-5.1-chat, etc.)
    payload["max_completion_tokens"] = self.max_tokens
```

## Testing

### Before Fix

Request with `max_tokens` and `temperature`:
- Status: 400 Bad Request
- Error: Unsupported parameter/value

### After Fix

Request with `max_completion_tokens` and no `temperature`:
- Status: 200 OK ✅
- Response: Successfully returns LLM completion

## Configuration Requirements

Ensure these environment variables are set correctly:

- `AZURE_AI_ENDPOINT` = `https://zimax-gw.azure-api.net/zimax` (base URL, no `/openai/v1/`)
- `AZURE_AI_DEPLOYMENT` = `gpt-5.1-chat`
- `AZURE_AI_API_VERSION` = `2024-12-01-preview` (required for gpt-5.1-chat)
- `AZURE_AI_MODEL_ROUTER` = *(empty or not set)*
- `AZURE_AI_KEY` = *(API key from Key Vault)*

## Model Compatibility Matrix

| Model | max_tokens | max_completion_tokens | temperature | API Version |
|-------|-----------|---------------------|-------------|-------------|
| `gpt-4`, `gpt-35-turbo` | ✅ | ❌ | ✅ (custom) | `2024-05-01-preview` |
| `gpt-5.1-chat` | ❌ | ✅ | ❌ (default only) | `2024-12-01-preview` |

## Key Learnings

1. **Model-specific parameters**: Different models may require different API parameters
2. **API version matters**: Newer models require newer API versions
3. **Backward compatibility**: Need to handle both old and new parameter formats
4. **Testing is critical**: Direct API testing helps identify parameter mismatches quickly

## Related Documentation

- `docs/troubleshooting/api-version-model-version-mismatch.md` - API version issues
- `docs/troubleshooting/chat-error-diagnosis.md` - General chat troubleshooting
- `docs/configuration/config-alignment.md` - Configuration reference
"""

# Add documentation as a system message
MESSAGES.append({
    "role": "system",
    "content": DOC_CONTENT,
    "metadata": {"type": "documentation", "source": "docs/troubleshooting/gpt-5.1-chat-api-parameters-fix.md"}
})


async def main():
    """Ingest the GPT-5.1-chat API parameters fix episode into Zep memory"""
    print("=" * 80)
    print("Ingesting GPT-5.1-chat API Parameters Fix Episode")
    print("=" * 80)
    print(f"ZEP URL: {ZEP_URL}")
    print(f"Session ID: {SESSION_ID}")
    print()
    
    client = ZepMemoryClient()
    
    try:
        # Create or get session
        print(f"📝 Creating session: {SESSION_ID}")
        await client.get_or_create_session(
            session_id=SESSION_ID,
            user_id=USER_ID,
            metadata=METADATA
        )
        print("   ✅ Session created/found")
        
        # Add messages
        print(f"\n💬 Adding {len(MESSAGES)} messages to memory...")
        await client.add_memory(
            session_id=SESSION_ID,
            messages=MESSAGES,
            metadata={"source": "ingest_gpt_5_1_chat_api_parameters_fix", "ingested_at": datetime.utcnow().isoformat()}
        )
        print("   ✅ Messages added")
        
        print(f"\n📄 Documentation content is included in episode and will be searchable via semantic search")
        
        print("\n" + "=" * 80)
        print("✅ Memory enrichment complete!")
        print(f"   Session: {SESSION_ID}")
        print(f"   Messages: {len(MESSAGES)}")
        print(f"   Topics: {', '.join(METADATA['topics'][:5])}...")
        print("=" * 80)
        print("\n💡 Agents can now reference this when:")
        print("   - Troubleshooting chat endpoint failures")
        print("   - Configuring new models")
        print("   - Understanding model-specific API requirements")
        print("   - Planning model upgrades")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

