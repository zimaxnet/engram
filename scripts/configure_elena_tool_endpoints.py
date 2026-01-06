#!/usr/bin/env python3
"""
Configure Elena's tool endpoints in Azure AI Foundry

This script updates Elena's agent definition in Foundry to include
endpoint URLs for all her tools, pointing to Engram's tool endpoints.

Prerequisites:
    - Azure CLI installed and logged in: az login
    - Foundry project access
    - Elena agent created in Foundry (Agent ID: Elena)
    - requests library: pip install requests

Usage:
    python scripts/configure_elena_tool_endpoints.py
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

# All Elena tools
TOOLS = [
    "analyze_requirements",
    "stakeholder_mapping",
    "create_user_story",
    "trigger_ingestion",
    "run_golden_thread",
    "search_memory",
    "delegate_to_sage",
    "send_email",
    "list_emails",
    "list_onedrive_files",
    "save_to_onedrive",
    "create_github_issue",
    "update_github_issue",
    "get_project_status",
    "list_my_tasks",
    "close_task",
]


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


def create_agent_version(token, agent_data):
    """Create a new agent version with updated tool endpoints."""
    # Foundry requires creating a new version, not updating the agent
    # Extract the definition from versions.latest.definition
    if "versions" in agent_data and "latest" in agent_data["versions"]:
        definition = agent_data["versions"]["latest"]["definition"]
        version_id = agent_data["versions"]["latest"]["id"]  # e.g., "Elena:1"
    else:
        definition = agent_data.get("definition", {})
        version_id = None
    
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


def configure_tool_endpoints(agent_data):
    """Configure tool endpoints in agent definition."""
    # Foundry returns agent with versions structure
    # definition is under versions.latest.definition
    if "versions" in agent_data and "latest" in agent_data["versions"]:
        definition = agent_data["versions"]["latest"]["definition"]
    elif "definition" in agent_data:
        definition = agent_data["definition"]
    else:
        print("❌ Agent definition not found in response")
        print(json.dumps(agent_data, indent=2))
        sys.exit(1)
    
    if "tools" not in definition:
        print("⚠️  No tools found in agent definition")
        return False
    
    tools = definition["tools"]
    updated_count = 0
    
    print(f"\nConfiguring {len(tools)} tools...")
    print("-" * 60)
    
    for tool in tools:
        tool_name = tool.get("name", "")
        if not tool_name:
            continue
        
        # Configure endpoint
        tool["endpoint"] = {
            "url": f"{TOOL_BASE_URL}/{tool_name}",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json"
            }
        }
        
        updated_count += 1
        print(f"  ✅ {tool_name:30s} → {TOOL_BASE_URL}/{tool_name}")
    
    print("-" * 60)
    print(f"✅ Configured {updated_count} tools")
    
    return updated_count > 0


def main():
    """Main function."""
    print("=" * 60)
    print("Configuring Elena Tool Endpoints in Azure AI Foundry")
    print("=" * 60)
    print(f"\nEndpoint: {ENDPOINT}")
    print(f"Agent: {AGENT_NAME}")
    print(f"Tool Base URL: {TOOL_BASE_URL}")
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
    
    # Configure tool endpoints
    if not configure_tool_endpoints(agent_data):
        print("⚠️  No tools were configured")
        sys.exit(1)
    
    # Create new version with updated tool endpoints
    print("\nCreating new agent version with tool endpoints...")
    try:
        new_version = create_agent_version(token, agent_data)
        version_id = new_version.get("id", "unknown")
        print(f"✅ New agent version created: {version_id}")
        print(f"\nNote: This is version {new_version.get('version', '?')} of the agent.")
        print("The new version includes tool endpoint configurations.")
    except Exception as e:
        print(f"⚠️  Failed to create new version: {e}")
        print("\nAlternative: Tool endpoints may need to be configured manually.")
        print("You can configure them in the Azure Portal:")
        print("  Azure AI Foundry → Project 'zimax' → Applications → 'Elena' → Tools")
        print("\nOr use the Azure AI Projects SDK to configure endpoints programmatically.")
        sys.exit(1)
    print()
    
    print("=" * 60)
    print("✅ Tool endpoint configuration complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Verify tool endpoints in Azure Portal:")
    print("   Azure AI Foundry → Project 'zimax' → Applications → 'Elena'")
    print()
    print("2. Test a tool endpoint:")
    print(f"   curl -X POST {TOOL_BASE_URL}/send_email \\")
    print("     -H 'Authorization: Bearer <token>' \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"to\": \"test@example.com\", \"subject\": \"Test\", \"body\": \"Hello\"}'")
    print()
    print("3. Enable Foundry Elena in Engram:")
    print("   export USE_FOUNDRY_ELENA=true")
    print("   export ELENA_FOUNDRY_AGENT_ID=Elena")
    print()


if __name__ == "__main__":
    main()

