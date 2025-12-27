#!/usr/bin/env python3
"""
Ingest the Model Router conversation thread into Zep Memory

This script ingests the conversation about configuring Azure AI Foundry
Model Router for chat, ensuring it's separate from VoiceLive configuration.
"""

import asyncio
import sys
from pathlib import Path
import os
from datetime import datetime, timezone

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.memory.client import ZepMemoryClient
from backend.core import get_settings

# Conversation thread content
CONVERSATION_MESSAGES = [
    {
        "role": "user",
        "content": "we also have responses api from openai import OpenAI\n\nendpoint = \"https://zimax-gw.azure-api.net/zimax/openai/v1/\"\ndeployment_name = \"model-router\"\napi_key = \"<your-api-key>\"\n\nclient = OpenAI(\n    base_url=endpoint,\n    api_key=api_key\n)\n\nresponse = client.responses.create(\n    model=deployment_name,\n    input=\"What is the capital of France?\",\n)\n\nprint(f\"answer: {response.output[0]}\")"
    },
    {
        "role": "assistant",
        "content": "Noting the responses API is also available via the Model Router. Updating the documentation to include both endpoints."
    },
    {
        "role": "user",
        "content": "To be clear, this is only for a chat. This should not affect in any way the voice live configuration."
    },
    {
        "role": "assistant",
        "content": "Confirmed: VoiceLive uses separate configuration and is completely unaffected by the chat Model Router changes. Verified that VoiceLive uses its own dedicated settings (AZURE_VOICELIVE_*) and is independent from chat configuration (AZURE_AI_*)."
    }
]

# Summary of the conversation
CONVERSATION_SUMMARY = """
Azure AI Foundry Model Router Configuration for Chat

This conversation covers configuring Azure AI Foundry Model Router for chat
completions, ensuring it's completely separate from VoiceLive configuration.

Key Points:
1. **Model Router via APIM Gateway**: Configured to use Model Router through
   APIM Gateway endpoint for intelligent model selection and cost optimization.

2. **Two APIs Available**:
   - Chat Completions API: Message-based format used by Engram agents
   - Responses API: Simpler input/output format for direct queries

3. **Configuration Separation**: 
   - Chat uses: AZURE_AI_ENDPOINT, AZURE_AI_MODEL_ROUTER, AZURE_AI_KEY
   - VoiceLive uses: AZURE_VOICELIVE_ENDPOINT, AZURE_VOICELIVE_KEY (completely separate)
   - No interference between chat and VoiceLive configurations

4. **Model Router Benefits**:
   - Dynamic model selection based on query complexity
   - Cost optimization (routes simple queries to cheaper models)
   - Automatic fallback and load balancing
   - Single endpoint for multiple models
   - Works with APIM Gateway for unified access control and monitoring

5. **Implementation**:
   - Updated FoundryChatClient to support Model Router via APIM Gateway
   - Model Router works with both APIM Gateway (recommended) and Foundry direct
   - Chat agents (Elena, Marcus, Sage) use Chat Completions API through Model Router
   - VoiceLive remains completely independent with its own configuration

Status: Complete - Model Router configured for chat, VoiceLive unaffected.
"""


async def ingest_model_router_conversation():
    """Ingest the Model Router conversation thread into Zep memory."""
    
    zep_url = os.getenv("ZEP_API_URL")
    if not zep_url:
        settings = get_settings()
        zep_url = settings.zep_api_url
    
    if not zep_url:
        print("❌ ZEP_API_URL not configured")
        print("   Set ZEP_API_URL environment variable")
        print("   Example: export ZEP_API_URL=https://zep-app.internal:8000")
        return False
    
    # Temporarily override settings for this script
    settings = get_settings()
    if zep_url:
        settings.zep_api_url = zep_url
    
    client = ZepMemoryClient()
    
    session_id = "sess-model-router-config-2024-12-20"
    user_id = "derek@zimax.net"
    
    print("=" * 60)
    print("Ingesting Model Router Configuration Conversation into Zep")
    print("=" * 60)
    print(f"\n   Session ID: {session_id}")
    print(f"   Messages: {len(CONVERSATION_MESSAGES)}")
    print(f"   Topics: Model Router, Chat Configuration, APIM Gateway, VoiceLive Separation")
    print(f"   Zep URL: {settings.zep_api_url}")
    print()
    
    # Create session with metadata
    metadata = {
        "summary": CONVERSATION_SUMMARY.strip(),
        "topics": [
            "Model Router",
            "Azure AI Foundry",
            "APIM Gateway",
            "Chat Configuration",
            "VoiceLive Separation",
            "Chat Completions API",
            "Responses API",
            "Cost Optimization",
            "Dynamic Model Selection"
        ],
        "agent_id": "antigravity-ai",
        "source": "conversation_ingestion",
        "thread_type": "configuration",
        "date": "2024-12-20",
        "turn_count": len(CONVERSATION_MESSAGES),
        "related_docs": [
            "backend/agents/base.py",
            "backend/core/config.py",
            "docs/sop/azure-ai-configuration.md",
            "backend/voice/voicelive_service.py"
        ],
        "key_changes": [
            "Added Model Router support via APIM Gateway",
            "Documented Chat Completions and Responses APIs",
            "Confirmed VoiceLive configuration separation"
        ]
    }
    
    try:
        # Create or get session
        print("📝 Creating/getting Zep session...")
        session = await client.get_or_create_session(
            session_id=session_id,
            user_id=user_id,
            metadata=metadata
        )
        print(f"   ✅ Session created/retrieved: {session_id}")
        
        # Format messages for Zep
        formatted_messages = []
        for msg in CONVERSATION_MESSAGES:
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["content"],
                "metadata": {
                    "source": "model_router_configuration_conversation",
                    "date": "2024-12-20",
                    "topic": "Model Router Configuration"
                }
            })
        
        # Add messages to session
        print(f"💾 Adding {len(formatted_messages)} messages to session...")
        await client.add_memory(
            session_id=session_id,
            messages=formatted_messages,
            metadata={
                "ingested_at": datetime.now(timezone.utc).isoformat(),
                "source": "script_ingestion",
                "conversation_type": "model_router_configuration"
            }
        )
        print(f"✅ Added {len(formatted_messages)} messages to session")
        
        # Enrich memory with key concepts
        print("\n🧠 Enriching memory with key concepts...")
        enrichment_messages = [
            {
                "role": "system",
                "content": "Key Concept: Azure AI Foundry Model Router is configured for chat completions via APIM Gateway. It provides intelligent model selection, cost optimization, and automatic fallback. Configuration uses AZURE_AI_ENDPOINT, AZURE_AI_MODEL_ROUTER, and AZURE_AI_KEY."
            },
            {
                "role": "system",
                "content": "Key Concept: Model Router supports two APIs: Chat Completions API (message-based, used by Engram agents) and Responses API (simpler input/output format). Both are available through the Model Router via APIM Gateway."
            },
            {
                "role": "system",
                "content": "Key Concept: VoiceLive uses completely separate configuration from chat. VoiceLive uses AZURE_VOICELIVE_* environment variables and is not affected by Model Router or chat endpoint settings. This separation ensures no interference between chat and voice configurations."
            },
            {
                "role": "system",
                "content": "Key Concept: Model Router configuration is only for chat. It does not affect VoiceLive in any way. Chat agents (Elena, Marcus, Sage) use the Chat Completions API through Model Router, while VoiceLive uses its own dedicated endpoint and configuration."
            }
        ]
        
        await client.add_memory(
            session_id=session_id,
            messages=enrichment_messages,
            metadata={
                "ingested_at": datetime.now(timezone.utc).isoformat(),
                "source": "memory_enrichment",
                "type": "key_concepts"
            }
        )
        print("✅ Memory enriched with key concepts")
        
        print("\n" + "=" * 60)
        print("🎉 Conversation ingested and memory enriched successfully!")
        print("=" * 60)
        print(f"\n   Session ID: {session_id}")
        print(f"   Total Messages: {len(formatted_messages) + len(enrichment_messages)}")
        print(f"\n   Agents can now reference this conversation when discussing:")
        print(f"   - Model Router configuration for chat")
        print(f"   - APIM Gateway integration")
        print(f"   - Chat Completions vs Responses APIs")
        print(f"   - VoiceLive configuration separation")
        print(f"   - Cost optimization through intelligent routing")
        
    except Exception as e:
        print(f"\n❌ Error ingesting conversation: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    asyncio.run(ingest_model_router_conversation())

