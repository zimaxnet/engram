#!/usr/bin/env python3
"""
Ingest VoiceLive Configuration Conversation into Zep Memory

This script ingests the entire VoiceLive configuration and troubleshooting
conversation thread into Zep as a session/episode for future reference.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.memory.client import ZepMemoryClient
from backend.core import get_settings

# Conversation thread content
VOICELIVE_CONVERSATION = [
    {
        "role": "user",
        "content": "Use the command line to test voice live on the SWA that has been deployed to azure"
    },
    {
        "role": "assistant",
        "content": "I'll help you test VoiceLive on the deployed Azure Static Web App. Let me create a test script to check the VoiceLive endpoints and configuration."
    },
    {
        "role": "user",
        "content": "Speaking with Dr. Elena Vasquez - Voice connection error - Failed to fetch"
    },
    {
        "role": "assistant",
        "content": "I see there's a voice connection error with 'Failed to fetch'. This suggests the frontend can't reach the backend API. Let me diagnose the issue by checking CORS configuration, authentication settings, and backend connectivity."
    },
    {
        "role": "user",
        "content": "Test again and let's get the whole author required or the 401 unauthorized errors fixed"
    },
    {
        "role": "assistant",
        "content": "I'll fix the 401 Unauthorized errors. The issue is likely Azure Container Apps Platform Authentication (EasyAuth) intercepting requests. I'll disable it and ensure AUTH_REQUIRED=false is set correctly."
    },
    {
        "role": "user",
        "content": "Failed to get ephemeral token: 400 we need to work on the Voice live configuration SOP and get the 400 air sorted out so that we can have a usable proper concept for customers to use Voice live"
    },
    {
        "role": "assistant",
        "content": "I'll fix the 400 Bad Request error on the token endpoint. The issue is incorrect endpoint URL construction for unified endpoints. I'll update the backend to correctly handle unified vs direct endpoints and improve error logging."
    },
    {
        "role": "user",
        "content": "Build the docker images, locally and test"
    },
    {
        "role": "assistant",
        "content": "I'll build the Docker images locally and test them. The Docker image builds successfully, and the API endpoints are working. The token endpoint has a known limitation with unified endpoints (returns 404), but the WebSocket proxy endpoint works correctly."
    },
    {
        "role": "user",
        "content": "Tested configuration that would be working with the measure SWA navigation UI"
    },
    {
        "role": "assistant",
        "content": "I'll test the configuration that works with the deployed SWA. The backend is configured correctly with WebSocket proxy endpoint. The frontend needs to be updated to use the WebSocket proxy instead of the token endpoint."
    },
    {
        "role": "user",
        "content": "@docs/sop/voicelive-configuration.md Update the SOP with the working configuration get it deployed to AZURE update the configuration test locally if we can"
    },
    {
        "role": "assistant",
        "content": "I'll update the SOP with the working configuration, deploy it to Azure, and test locally. Updated the SOP to document WebSocket proxy as the production approach, added missing environment variables to Bicep, updated Azure Container App configuration, and verified with local Docker testing."
    },
    {
        "role": "user",
        "content": "Are we able to use the updated voice live API version?"
    },
    {
        "role": "assistant",
        "content": "Yes! I've updated to API version 2025-10-01, which includes 140+ languages, Neural HD voices, improved VAD, and 4K avatar support. Updated backend code, infrastructure, Azure deployment, and documentation. All systems are now using the latest API version."
    },
    {
        "role": "user",
        "content": "Create a JASON file with detailed information for nano banana Pro to create a diagram for what where doing with Voice live web socket proxy and then also ensure that the text being ingested into ZEP memory is included"
    },
    {
        "role": "assistant",
        "content": "I'll create a comprehensive JSON diagram file for Nano Banana Pro showing the VoiceLive WebSocket proxy architecture with Zep memory ingestion. The diagram includes all components, data flows, audio streaming, transcript extraction, and automatic memory persistence to Zep episodic memory."
    },
    {
        "role": "user",
        "content": "What folder should the PNG file be placed in four the documentation to reference this image?"
    },
    {
        "role": "assistant",
        "content": "The PNG file should be placed in `docs/assets/diagrams/` and referenced as `/assets/diagrams/voicelive-websocket-proxy-architecture.png` in markdown files. This matches the existing diagram structure and JSON file location."
    },
    {
        "role": "user",
        "content": "The diagram is placed in the specified location. Please create documentation that references it."
    },
    {
        "role": "assistant",
        "content": "I'll add diagram references to the VoiceLive configuration SOP. Added the diagram in the Architecture section with a detailed caption, and created a dedicated 'Architecture Diagram' section with comprehensive explanation of all components and flows shown in the diagram."
    },
    {
        "role": "user",
        "content": "Is Voice live validated to be functioning from the SWA that is deployed in Azure"
    },
    {
        "role": "assistant",
        "content": "VoiceLive backend is configured and ready, but the frontend needs to be updated. The frontend currently uses the token endpoint which doesn't work with unified endpoints. I've created a validation status document showing what's ready and what needs to be done."
    },
    {
        "role": "user",
        "content": "Proceed with the updates so that Voice can be validated to be working"
    },
    {
        "role": "assistant",
        "content": "I'll update the frontend to use the WebSocket proxy endpoint. Updated VoiceChat.tsx to connect directly to backend WebSocket proxy, removed token endpoint dependency, updated message format to match backend protocol, added agent switching support, and verified the frontend builds successfully."
    },
    {
        "role": "user",
        "content": "If I understand correctly, the voice has to proxy through the backend to get to the SWA now"
    },
    {
        "role": "assistant",
        "content": "Let me clarify: The SWA IS the frontend (runs in browser). The flow is: Browser (SWA Frontend) → Backend WebSocket Proxy → Azure VoiceLive. The backend proxies BETWEEN the browser and Azure, not between Azure and the SWA. Created an architecture clarification document to explain this."
    },
    {
        "role": "user",
        "content": "Commit the updates and push so that the deployment can be done and we can validate"
    },
    {
        "role": "assistant",
        "content": "I'll commit and push all the VoiceLive updates. Committed 17 files with VoiceLive WebSocket proxy implementation, API version 2025-10-01 update, frontend updates, infrastructure changes, and comprehensive documentation. Changes are pushed and ready for deployment."
    },
    {
        "role": "user",
        "content": "Ingest this entire voice live thread into zep either as a session or an episode"
    },
    {
        "role": "assistant",
        "content": "I'll create a script to ingest this entire VoiceLive conversation thread into Zep memory as a session/episode for future reference and context retrieval."
    }
]

# Summary of the conversation
CONVERSATION_SUMMARY = """
VoiceLive Configuration and Deployment - Complete Thread

This conversation covers the complete journey of configuring, troubleshooting, and deploying VoiceLive for the Engram platform:

Key Topics:
- Initial testing of VoiceLive on Azure SWA deployment
- Diagnosing and fixing 401 Unauthorized errors (EasyAuth, AUTH_REQUIRED)
- Fixing 400 Bad Request errors on token endpoint (unified endpoint path issues)
- Building and testing Docker images locally
- Updating to API version 2025-10-01 (latest with enhanced features)
- Creating comprehensive architecture diagrams
- Updating frontend to use WebSocket proxy endpoint
- Architecture clarification (SWA = frontend, backend = proxy)
- Complete deployment and validation preparation

Technical Achievements:
- Backend configured with WebSocket proxy for unified endpoints
- Frontend updated to connect via WebSocket proxy
- API version upgraded to 2025-10-01
- Comprehensive documentation and diagrams created
- All changes committed and pushed for deployment

Status: Ready for deployment and end-to-end validation
"""


async def ingest_voicelive_conversation():
    """Ingest the VoiceLive conversation thread into Zep memory."""
    import os
    
    # Allow override via environment variable
    zep_url = os.getenv("ZEP_API_URL")
    if not zep_url:
        settings = get_settings()
        zep_url = settings.zep_api_url
    
    if not zep_url:
        print("❌ ZEP_API_URL not configured")
        print("   Set ZEP_API_URL environment variable")
        print("   Example: export ZEP_API_URL=https://zep-app.internal:8000")
        return
    
    # Temporarily override settings for this script
    from backend.core import get_settings
    settings = get_settings()
    if zep_url:
        settings.zep_api_url = zep_url
    
    client = ZepMemoryClient()
    
    session_id = "voicelive-configuration-thread-2025-12-27"
    user_id = "derek@zimax.net"
    
    print("=" * 60)
    print("Ingesting VoiceLive Configuration Conversation into Zep")
    print("=" * 60)
    print(f"\nSession ID: {session_id}")
    print(f"User ID: {user_id}")
    print(f"Messages: {len(VOICELIVE_CONVERSATION)}")
    print(f"Zep URL: {settings.zep_api_url}")
    print()
    
    # Create session with metadata
    metadata = {
        "summary": CONVERSATION_SUMMARY.strip(),
        "topics": [
            "VoiceLive",
            "WebSocket Proxy",
            "Azure Deployment",
            "Configuration",
            "Troubleshooting",
            "API Version 2025-10-01",
            "Frontend Integration",
            "Memory Persistence"
        ],
        "agent_id": "elena",
        "source": "conversation_ingestion",
        "thread_type": "configuration_and_deployment",
        "date": "2025-12-27",
        "turn_count": len(VOICELIVE_CONVERSATION)
    }
    
    try:
        # Create or get session
        print("📝 Creating/getting Zep session...")
        session = await client.get_or_create_session(
            session_id=session_id,
            user_id=user_id,
            metadata=metadata
        )
        print(f"   ✅ Session: {session_id}")
        
        # Format messages for Zep
        formatted_messages = []
        for msg in VOICELIVE_CONVERSATION:
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["content"],
                "metadata": {
                    "source": "voice_live_configuration_thread",
                    "date": "2025-12-27"
                }
            })
        
        # Add messages to session
        print(f"\n💾 Adding {len(formatted_messages)} messages to memory...")
        await client.add_memory(
            session_id=session_id,
            messages=formatted_messages,
            metadata={
                "ingested_at": "2025-12-27T20:30:00Z",
                "source": "script_ingestion",
                "conversation_type": "voice_live_configuration"
            }
        )
        print(f"   ✅ Added {len(formatted_messages)} messages")
        
        print("\n" + "=" * 60)
        print("✅ Conversation ingested successfully!")
        print("=" * 60)
        print(f"\nSession ID: {session_id}")
        print(f"Total Messages: {len(formatted_messages)}")
        print(f"\nYou can now search for this conversation in Zep using:")
        print(f"  - Session ID: {session_id}")
        print(f"  - Topics: VoiceLive, WebSocket Proxy, Configuration")
        print(f"  - Summary keywords: VoiceLive configuration, deployment, troubleshooting")
        
    except Exception as e:
        print(f"\n❌ Error ingesting conversation: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    asyncio.run(ingest_voicelive_conversation())

