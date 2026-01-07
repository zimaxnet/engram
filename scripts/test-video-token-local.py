#!/usr/bin/env python3
"""
Test Video Token Generation Locally

Tests the video token generation with Managed Identity and multiple API versions.

Usage:
    python scripts/test-video-token-local.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.api.routers.voice import TokenRequest, get_realtime_token
from backend.core import get_settings


async def test_video_token_generation():
    """Test video token generation locally."""
    print("=" * 60)
    print("Testing Video Token Generation (Local)")
    print("=" * 60)
    print()
    
    settings = get_settings()
    
    print("Configuration:")
    print(f"  Endpoint: {settings.azure_voicelive_endpoint}")
    print(f"  Project: {settings.azure_voicelive_project_name}")
    print(f"  Model: {settings.azure_voicelive_model}")
    print(f"  API Version: {settings.azure_voicelive_api_version}")
    print()
    
    if not settings.azure_voicelive_endpoint:
        print("❌ VoiceLive endpoint not configured")
        return False
    
    # Test video token generation
    print("Test: Video token generation with modalities=['video', 'text']")
    print("-" * 60)
    
    try:
        request = TokenRequest(
            agent_id="elena",
            modalities=["video", "text"]
        )
        
        print(f"Request:")
        print(f"  agent_id: {request.agent_id}")
        print(f"  modalities: {request.modalities}")
        print()
        print("Generating token...")
        
        response = await get_realtime_token(request)
        
        print("✅ Token generated successfully!")
        print(f"   Endpoint: {response.endpoint}")
        print(f"   Token length: {len(response.token)} chars")
        print(f"   Expires at: {response.expires_at}")
        print()
        print("=" * 60)
        print("✅ Video token generation works!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print()
        print("=" * 60)
        print("❌ Video token generation failed")
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = asyncio.run(test_video_token_generation())
    sys.exit(0 if success else 1)

