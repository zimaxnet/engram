#!/usr/bin/env python3
"""
CLI tool to generate VoiceLive tokens using Managed Identity.

This script uses Azure Managed Identity (DefaultAzureCredential) to generate
tokens for VoiceLive connections. Useful for testing and debugging.

Usage:
    python scripts/generate-voicelive-token-cli.py [--agent elena] [--modalities video,text]
    python scripts/generate-voicelive-token-cli.py --agent elena --modalities video,text --output json
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from azure.identity import DefaultAzureCredential
from backend.core import get_settings
from backend.voice.voicelive_service import voicelive_service
from backend.api.routers.voice import _generate_token_with_failsafe, validate_voicelive_endpoint


async def generate_token_cli(
    agent_id: str = "elena",
    modalities: list[str] = None,
    output_format: str = "human",
) -> dict:
    """
    Generate a VoiceLive token using Managed Identity via CLI.
    
    Args:
        agent_id: Agent ID (elena, marcus, sage)
        modalities: List of modalities (default: ["video", "text"])
        output_format: Output format ("human" or "json")
    
    Returns:
        Dictionary with token information
    """
    if modalities is None:
        modalities = ["video", "text"]
    
    print("=" * 70)
    print("VoiceLive Token Generation (Managed Identity)")
    print("=" * 70)
    print()
    
    # Get settings
    settings = get_settings()
    
    # Validate VoiceLive configuration
    if not voicelive_service.is_configured:
        print("❌ Error: VoiceLive not configured")
        print("   Set AZURE_VOICELIVE_ENDPOINT and AZURE_VOICELIVE_KEY")
        sys.exit(1)
    
    endpoint = voicelive_service.endpoint.rstrip('/')
    is_valid, endpoint_type = validate_voicelive_endpoint(endpoint)
    
    if not is_valid:
        print(f"❌ Error: Invalid VoiceLive endpoint format: {endpoint}")
        sys.exit(1)
    
    # Get agent configuration
    try:
        agent_config = voicelive_service.get_agent_voice_config(agent_id)
    except Exception as e:
        print(f"❌ Error: Invalid agent ID '{agent_id}': {e}")
        sys.exit(1)
    
    # Build session configuration
    session_config = {
        "model": voicelive_service.model,
        "modalities": modalities,
        "instructions": agent_config.instructions,
        "voice": agent_config.voice_name,
    }
    
    # Add avatar config if video is requested
    if "video" in modalities and agent_id == "elena":
        session_config["avatar"] = {
            "avatar_id": "en-US-JennyNeural",
            "style": "professional",
            "emotion": "neutral",
            "resolution": "1080p",
            "background": "transparent",
        }
    
    # Display configuration
    print("Configuration:")
    print(f"  Endpoint: {endpoint}")
    print(f"  Endpoint Type: {endpoint_type}")
    print(f"  Project: {voicelive_service.project_name or 'None'}")
    print(f"  Model: {voicelive_service.model}")
    print(f"  API Version: {voicelive_service.api_version}")
    print(f"  Agent: {agent_id}")
    print(f"  Modalities: {', '.join(modalities)}")
    print(f"  Voice: {agent_config.voice_name}")
    print()
    
    # Try to get credential
    print("Authenticating with Managed Identity...")
    try:
        credential = DefaultAzureCredential()
        # Test credential by getting a token
        token = credential.get_token("https://ai.azure.com/.default")
        print(f"✅ Managed Identity authentication successful")
        print(f"   Token expires at: {token.expires_on}")
        print()
    except Exception as e:
        print(f"❌ Error: Failed to authenticate with Managed Identity")
        print(f"   {str(e)}")
        print()
        print("Troubleshooting:")
        print("  1. Ensure you're running in an Azure environment (Container App, VM, etc.)")
        print("  2. Or use Azure CLI: 'az login'")
        print("  3. Or set environment variables: AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID")
        sys.exit(1)
    
    # Generate token using failsafe logic
    print("Generating token using failsafe strategy...")
    print()
    
    token_response = await _generate_token_with_failsafe(
        endpoint=endpoint,
        endpoint_type=endpoint_type,
        project_name=voicelive_service.project_name,
        api_version=voicelive_service.api_version,
        model=voicelive_service.model,
        session_config=session_config,
        voicelive_service=voicelive_service,
    )
    
    if not token_response:
        print("❌ Error: All token generation strategies failed")
        print()
        print("Troubleshooting:")
        print("  1. Check Managed Identity has 'Cognitive Services Speech User' role")
        print("  2. Verify endpoint is correct and accessible")
        print("  3. Check API version compatibility")
        print("  4. For local testing, set AZURE_VOICELIVE_KEY")
        sys.exit(1)
    
    # Output results
    if output_format == "json":
        result = {
            "token": token_response.token,
            "endpoint": token_response.endpoint,
            "expires_at": token_response.expires_at,
            "agent_id": agent_id,
            "modalities": modalities,
            "voice": agent_config.voice_name,
        }
        print(json.dumps(result, indent=2))
    else:
        print("=" * 70)
        print("✅ Token Generated Successfully")
        print("=" * 70)
        print()
        print("Token Details:")
        print(f"  Token (first 50 chars): {token_response.token[:50]}...")
        print(f"  Token length: {len(token_response.token)} characters")
        print(f"  Endpoint: {token_response.endpoint}")
        if token_response.expires_at:
            print(f"  Expires at: {token_response.expires_at}")
        print()
        print("Usage:")
        print("  Use this token in the 'Authorization: Bearer <token>' header")
        print("  Or as 'api-key: <token>' header for WebSocket connections")
        print()
        print("WebSocket Connection:")
        print(f"  {token_response.endpoint}")
        print()
        print("Example curl command:")
        print(f"  curl -H 'Authorization: Bearer {token_response.token[:20]}...' \\")
        print(f"       '{token_response.endpoint}'")
    
    return {
        "token": token_response.token,
        "endpoint": token_response.endpoint,
        "expires_at": token_response.expires_at,
    }


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate VoiceLive tokens using Managed Identity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate token for Elena with video
  python scripts/generate-voicelive-token-cli.py --agent elena --modalities video,text
  
  # Generate token for audio only
  python scripts/generate-voicelive-token-cli.py --agent elena --modalities audio,text
  
  # Output as JSON
  python scripts/generate-voicelive-token-cli.py --agent elena --output json
        """
    )
    
    parser.add_argument(
        "--agent",
        default="elena",
        choices=["elena", "marcus", "sage"],
        help="Agent ID (default: elena)"
    )
    
    parser.add_argument(
        "--modalities",
        default="video,text",
        help="Comma-separated list of modalities (default: video,text)"
    )
    
    parser.add_argument(
        "--output",
        default="human",
        choices=["human", "json"],
        help="Output format (default: human)"
    )
    
    args = parser.parse_args()
    
    # Parse modalities
    modalities = [m.strip() for m in args.modalities.split(",")]
    
    # Validate modalities
    valid_modalities = ["audio", "text", "video"]
    for mod in modalities:
        if mod not in valid_modalities:
            print(f"❌ Error: Invalid modality '{mod}'. Valid options: {', '.join(valid_modalities)}")
            sys.exit(1)
    
    # Generate token
    try:
        result = asyncio.run(generate_token_cli(
            agent_id=args.agent,
            modalities=modalities,
            output_format=args.output,
        ))
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

