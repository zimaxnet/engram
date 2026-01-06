#!/usr/bin/env python3
"""
Configure Elena's Avatar in Azure AI Foundry

This script configures Azure AI Foundry's TTS Avatar feature for Elena,
enabling photorealistic video avatars with natural voice and expressions.

Prerequisites:
    - Azure CLI installed and logged in: az login
    - Foundry project access
    - Elena agent created in Foundry (Agent ID: Elena)
    - requests library: pip install requests

Usage:
    python scripts/configure_elena_avatar.py
"""

import json
import subprocess
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import requests
except ImportError:
    print("❌ 'requests' library not found. Please install it:")
    print("   pip install requests")
    sys.exit(1)

# Configuration
ENDPOINT = "https://zimax.services.ai.azure.com/api/projects/zimax"
AGENT_NAME = "Elena"
API_VERSION = "2025-11-15-preview"
TOOL_BASE_URL = "https://engram.work/api/v1/tools"

# Elena's avatar configuration
# Using standard Azure TTS Avatar (can be customized later)
AVATAR_CONFIG = {
    "avatar_id": "en-US-JennyNeural",  # Matches Elena's voice
    "style": "professional",  # Professional business analyst style
    "emotion": "neutral",  # Can be: neutral, happy, sad, angry, etc.
    "resolution": "1080p",  # Options: 720p, 1080p, 4K
    "background": "transparent",  # transparent or custom background
}


def get_access_token():
    """Get Azure access token using Azure CLI."""
    try:
        result = subprocess.run(
            [
                "az", "account", "get-access-token",
                "--resource", "https://ai.azure.com",
                "--query", "accessToken",
                "-o", "tsv"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        token = result.stdout.strip()
        if not token:
            raise ValueError("Empty token received")
        return token
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to get access token: {e}")
        print("Please ensure you're logged in: az login")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error getting access token: {e}")
        sys.exit(1)


def get_agent(token):
    """Get current agent definition from Foundry."""
    url = f"{ENDPOINT}/agents/{AGENT_NAME}?api-version={API_VERSION}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to get agent: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        sys.exit(1)


def configure_avatar(agent_data):
    """Configure avatar settings in agent definition."""
    # Foundry returns agent with versions structure
    if "versions" in agent_data and "latest" in agent_data["versions"]:
        definition = agent_data["versions"]["latest"]["definition"]
    elif "definition" in agent_data:
        definition = agent_data["definition"]
    else:
        print("❌ Agent definition not found in response")
        print(json.dumps(agent_data, indent=2))
        sys.exit(1)
    
    # Add avatar configuration to definition
    if "avatar" not in definition:
        definition["avatar"] = {}
    
    definition["avatar"].update(AVATAR_CONFIG)
    
    print(f"\nConfiguring avatar...")
    print("-" * 60)
    print(f"  Avatar ID: {AVATAR_CONFIG['avatar_id']}")
    print(f"  Style: {AVATAR_CONFIG['style']}")
    print(f"  Emotion: {AVATAR_CONFIG['emotion']}")
    print(f"  Resolution: {AVATAR_CONFIG['resolution']}")
    print(f"  Background: {AVATAR_CONFIG['background']}")
    print("-" * 60)
    print("✅ Avatar configuration added")
    
    return True


def create_agent_version(token, agent_data):
    """Create a new agent version with avatar configuration."""
    # Extract the definition from versions.latest.definition
    if "versions" in agent_data and "latest" in agent_data["versions"]:
        definition = agent_data["versions"]["latest"]["definition"]
    else:
        definition = agent_data.get("definition", {})
    
    # Create new version endpoint
    url = f"{ENDPOINT}/agents/{AGENT_NAME}/versions?api-version={API_VERSION}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Payload for new version
    payload = {
        "definition": definition
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json() if response.content else {}
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to create agent version: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        raise


def main():
    """Main function."""
    print("=" * 60)
    print("Configuring Elena Avatar in Azure AI Foundry")
    print("=" * 60)
    print(f"\nEndpoint: {ENDPOINT}")
    print(f"Agent: {AGENT_NAME}")
    print()
    
    # Get access token
    print("Getting access token...")
    token = get_access_token()
    print("✅ Access token obtained")
    print()
    
    # Get current agent
    print("Fetching current agent definition...")
    agent_data = get_agent(token)
    print(f"✅ Retrieved agent: {agent_data.get('name', AGENT_NAME)}")
    print()
    
    # Configure avatar
    if not configure_avatar(agent_data):
        print("⚠️  Avatar configuration failed")
        sys.exit(1)
    
    # Create new version with avatar
    print("\nCreating new agent version with avatar configuration...")
    try:
        new_version = create_agent_version(token, agent_data)
        version_id = new_version.get("id", "unknown")
        version_num = new_version.get("version", "?")
        print(f"✅ New agent version created: {version_id}")
        print(f"   Version: {version_num}")
        print(f"\n✅ Avatar configuration complete!")
    except Exception as e:
        print(f"⚠️  Failed to create new version: {e}")
        print("\nAlternative: Avatar may need to be configured manually.")
        print("You can configure it in the Azure Portal:")
        print("  Azure AI Foundry → Project 'zimax' → Applications → 'Elena' → Avatar")
        print("\nOr use the Azure AI Projects SDK to configure avatar programmatically.")
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("✅ Avatar Configuration Complete!")
    print("=" * 60)
    print("\nAvatar Features:")
    print("  ✅ Photorealistic video avatar")
    print("  ✅ Natural voice (en-US-JennyNeural)")
    print("  ✅ Emotion control")
    print("  ✅ 1080p resolution (upgradeable to 4K)")
    print()
    print("Next steps:")
    print("1. Test avatar in Azure Portal:")
    print("   Azure AI Foundry → Project 'zimax' → Applications → 'Elena' → Test")
    print()
    print("2. Use avatar in responses:")
    print("   The avatar will automatically generate video when Elena responds")
    print()
    print("3. Customize avatar (optional):")
    print("   - Create custom avatar with Elena's likeness")
    print("   - Adjust emotions and expressions")
    print("   - Upgrade to 4K resolution")
    print()


if __name__ == "__main__":
    main()

