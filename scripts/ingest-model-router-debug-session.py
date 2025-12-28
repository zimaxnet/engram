#!/usr/bin/env python3
"""
Ingest the Model Router Debugging Session into Zep Memory

This script creates an episodic memory of the December 27, 2025 debugging session
that resolved the chat integration issues with Azure AI Foundry Model Router.

Key learnings:
1. Azure OpenAI format vs OpenAI SDK format
2. APIM gateway requires base URL only (no /openai/v1)
3. Platform Authentication must be disabled for public API access
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.memory.client import memory_client

SESSION_ID = "sess-model-router-debug-20251227"

CONVERSATION = [
    {
        "role": "user",
        "role_type": "user",
        "content": "Chat is not working with model-router. Elena returns: 'I apologize, but I encountered an issue processing your request.'"
    },
    {
        "role": "assistant",
        "role_type": "assistant",
        "content": "Investigating the Azure Container App logs. Found the error: 401 PermissionDenied when calling https://zimax.services.ai.azure.com/api/projects/zimax/openai/deployments/gpt-4o/chat/completions. The endpoint configuration is wrong."
    },
    {
        "role": "user",
        "role_type": "user",
        "content": "The Model Router deployment URL is: https://zimax-gw.azure-api.net/zimax/openai/deployments/model-router/chat/completions?api-version=2024-05-01-preview"
    },
    {
        "role": "assistant",
        "role_type": "assistant", 
        "content": "Key insight: The APIM gateway uses Azure OpenAI SDK format (deployment in URL path), not OpenAI SDK format (/openai/v1 with model in body). Correcting the endpoint to base URL only: https://zimax-gw.azure-api.net/zimax"
    },
    {
        "role": "assistant",
        "role_type": "assistant",
        "content": "Updated Azure Container App environment variables via CLI: AZURE_AI_ENDPOINT=https://zimax-gw.azure-api.net/zimax, AZURE_AI_DEPLOYMENT=model-router, AZURE_AI_PROJECT_NAME= (empty), AZURE_AI_API_VERSION=2024-05-01-preview"
    },
    {
        "role": "assistant",
        "role_type": "assistant",
        "content": "Still getting 401 error, but now from Azure Platform Authentication (EasyAuth), not the API. The www-authenticate header shows Bearer authentication is enabled at the platform level."
    },
    {
        "role": "assistant",
        "role_type": "assistant",
        "content": "Disabled Azure Platform Auth with: az containerapp auth update --name staging-env-api --resource-group engram-rg --unauthenticated-client-action AllowAnonymous --enabled false"
    },
    {
        "role": "assistant",
        "role_type": "assistant",
        "content": "SUCCESS! Chat is now working. Elena responded: 'Hello! It's great to connect with you. How can I assist you today?'"
    }
]

SUMMARY = """
Model Router Chat Debugging Session - December 27, 2025

This session resolved critical chat integration issues with Azure AI Foundry Model Router.

## Root Causes Identified

1. **Wrong Endpoint Format**: Configuration used OpenAI SDK format (/openai/v1) but APIM gateway requires Azure OpenAI SDK format (base URL only)

2. **Wrong Endpoint**: Was using https://zimax.services.ai.azure.com (Foundry direct) instead of https://zimax-gw.azure-api.net/zimax (APIM gateway)

3. **Platform Auth Blocking**: Azure Container Apps EasyAuth was enabled and blocking unauthenticated requests

## Solution Applied

1. Set AZURE_AI_ENDPOINT to base URL: https://zimax-gw.azure-api.net/zimax
2. Set AZURE_AI_DEPLOYMENT to model-router
3. Set AZURE_AI_API_VERSION to 2024-05-01-preview
4. Leave AZURE_AI_PROJECT_NAME empty
5. Disabled Azure Platform Auth (AllowAnonymous)

## Key Technical Insight

Azure OpenAI SDK format: {endpoint}/openai/deployments/{model}/chat/completions?api-version=...
OpenAI SDK format: {endpoint}/chat/completions with model in request body

The FoundryChatClient code detects which format to use based on whether the endpoint URL contains '/openai/v1'.

Status: Resolved - Chat verified working.
"""


async def ingest_session():
    """Ingest the debugging session into Zep memory."""
    print("=" * 60)
    print("Ingesting Model Router Debugging Session into Zep")
    print("=" * 60)
    print(f"Session ID: {SESSION_ID}")
    print(f"Messages: {len(CONVERSATION)}")
    print()

    client = memory_client
    if not client:
        print("ERROR: Could not get memory client")
        return

    try:
        # Create or get session
        try:
            await client.add_session(
                session_id=SESSION_ID,
                user_id="derek",
                metadata={
                    "type": "debugging",
                    "topic": "Model Router Chat Integration",
                    "date": "2025-12-27",
                    "status": "resolved",
                    "components": ["APIM", "Azure OpenAI", "Model Router", "FoundryChatClient"],
                }
            )
            print(f"✅ Created session: {SESSION_ID}")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"ℹ️  Session already exists: {SESSION_ID}")
            else:
                raise

        # Add conversation messages
        for i, msg in enumerate(CONVERSATION):
            await client.add_memory(
                session_id=SESSION_ID,
                messages=[{
                    "role": msg["role"],
                    "role_type": msg["role_type"],
                    "content": msg["content"],
                    "metadata": {
                        "sequence": i + 1,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                }]
            )
        print(f"✅ Added {len(CONVERSATION)} messages")

        # Add summary as a fact
        try:
            await client.add_memory(
                session_id=SESSION_ID,
                messages=[{
                    "role": "system",
                    "role_type": "system",
                    "content": SUMMARY,
                    "metadata": {
                        "type": "session_summary",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                }]
            )
            print("✅ Added session summary")
        except Exception as e:
            print(f"⚠️  Could not add summary: {e}")

        print()
        print("=" * 60)
        print("✅ Session ingested successfully!")
        print("=" * 60)
        print()
        print("Key information now in Zep memory:")
        print("  - Azure OpenAI vs OpenAI SDK format distinction")
        print("  - Correct APIM gateway endpoint configuration")
        print("  - Platform Auth troubleshooting steps")
        print("  - Model Router deployment details")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(ingest_session())
