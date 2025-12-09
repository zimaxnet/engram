#!/usr/bin/env python3
"""
Test VoiceLive Integration

Tests the VoiceLive service for both Elena and Marcus agents.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Set environment variables before imports
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("AZURE_AI_ENDPOINT", "https://zimax.services.ai.azure.com")
os.environ.setdefault("AZURE_AI_PROJECT_NAME", "zimax")
os.environ.setdefault("AZURE_OPENAI_KEY", os.getenv("AZURE_OPENAI_KEY", ""))
os.environ.setdefault("AZURE_VOICELIVE_MODEL", "gpt-realtime")
os.environ.setdefault("AZURE_VOICELIVE_VOICE", "en-US-Ava:DragonHDLatestNeural")
os.environ.setdefault("MARCUS_VOICELIVE_VOICE", "en-US-GuyNeural")

# Load from .env if exists
try:
    from dotenv import load_dotenv
    load_dotenv(backend_path.parent / ".env", override=True)
except ImportError:
    pass  # dotenv not required

async def test_voicelive_service():
    """Test VoiceLive service creation and configuration"""
    print("=" * 60)
    print("Testing VoiceLive Integration")
    print("=" * 60)
    print()
    
    try:
        from backend.voice.voicelive_service import voicelive_service
        from backend.core import get_settings
        
        settings = get_settings()
        
        print("✓ VoiceLive service imported successfully")
        print()
        
        # Check configuration
        print("Configuration Check:")
        print(f"  - Endpoint: {settings.azure_ai_endpoint or 'Not set'}")
        print(f"  - Project: {settings.azure_ai_project_name or 'Not set'}")
        print(f"  - OpenAI Key: {'Set' if settings.azure_openai_key else 'Not set'}")
        print(f"  - Model: {settings.azure_voicelive_model}")
        print(f"  - Elena Voice: {settings.azure_voicelive_voice}")
        print(f"  - Marcus Voice: {settings.marcus_voicelive_voice}")
        print()
        
        # Test endpoint property
        try:
            endpoint = voicelive_service.endpoint
            print(f"✓ Effective endpoint: {endpoint}")
        except Exception as e:
            print(f"✗ Endpoint error: {e}")
            return False
        
        # Test credential
        try:
            credential = voicelive_service.credential
            print(f"✓ Credential created: {type(credential).__name__}")
        except Exception as e:
            print(f"✗ Credential error: {e}")
            return False
        
        # Test Elena instructions
        elena_instructions = voicelive_service.get_elena_instructions()
        print(f"✓ Elena instructions: {len(elena_instructions)} characters")
        assert "Elena" in elena_instructions or "Business Analyst" in elena_instructions
        
        # Test Marcus instructions
        marcus_instructions = voicelive_service.get_marcus_instructions()
        print(f"✓ Marcus instructions: {len(marcus_instructions)} characters")
        assert "Marcus" in marcus_instructions or "Project Manager" in marcus_instructions
        
        print()
        print("=" * 60)
        print("✓ All basic tests passed!")
        print("=" * 60)
        print()
        print("Next: Test actual VoiceLive connection")
        print("  - Start backend: uvicorn backend.api.main:app --reload")
        print("  - Connect WebSocket to: ws://localhost:8082/api/v1/voice/voicelive/test-session")
        print()
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print()
        print("Install VoiceLive SDK:")
        print("  pip install azure-ai-voicelive")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_voicelive_connection():
    """Test actual VoiceLive connection (requires running backend)"""
    print("=" * 60)
    print("Testing VoiceLive Connection")
    print("=" * 60)
    print()
    print("This test requires the backend to be running.")
    print("Start it with: uvicorn backend.api.main:app --reload")
    print()
    
    import websockets
    import json
    
    try:
        uri = "ws://localhost:8082/api/v1/voice/voicelive/test-connection-123"
        print(f"Connecting to: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✓ WebSocket connected")
            
            # Send a test message
            await websocket.send(json.dumps({
                "type": "agent",
                "agent_id": "elena"
            }))
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)
            print(f"✓ Received: {data.get('type', 'unknown')}")
            
            return True
            
    except websockets.exceptions.InvalidURI:
        print("✗ Invalid WebSocket URI")
        return False
    except ConnectionRefusedError:
        print("✗ Connection refused - is the backend running?")
        print("  Start with: uvicorn backend.api.main:app --reload")
        return False
    except asyncio.TimeoutError:
        print("✗ Connection timeout")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test VoiceLive integration")
    parser.add_argument(
        "--connection",
        action="store_true",
        help="Test actual WebSocket connection (requires running backend)"
    )
    
    args = parser.parse_args()
    
    # Run basic tests
    success = asyncio.run(test_voicelive_service())
    
    if args.connection and success:
        print()
        asyncio.run(test_voicelive_connection())
    
    sys.exit(0 if success else 1)

