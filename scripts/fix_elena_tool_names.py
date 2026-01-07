#!/usr/bin/env python3
"""
Fix Elena's tool names in Foundry to match the required pattern.

This script updates Elena's agent definition to ensure all tool names
match Foundry's pattern: ^[a-zA-Z0-9_\.-]+$

Usage:
    python scripts/fix_elena_tool_names.py
"""

import json
import subprocess
import sys
import re
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


def get_access_token():
    """Get Azure access token using Azure CLI."""
    try:
        result = subprocess.run(
            ["az", "account", "get-access-token", "--resource", "https://ai.azure.com", "--query", "accessToken", "-o", "tsv"],
            capture_output=True,
            text=True,
            check=True
        )
        token = result.stdout.strip()
        if not token:
            print("❌ Failed to get access token")
            sys.exit(1)
        return token
    except subprocess.CalledProcessError as e:
        print(f"❌ Azure CLI error: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Azure CLI not found. Please install it first.")
        sys.exit(1)


def sanitize_tool_name(name: str) -> str:
    """
    Sanitize tool name to match Foundry pattern: ^[a-zA-Z0-9_\.-]+$
    Replace any invalid characters with underscores.
    """
    # Pattern: only letters, numbers, underscores, dots, and hyphens
    sanitized = re.sub(r'[^a-zA-Z0-9_\.-]', '_', name)
    return sanitized


def fix_tool_names(agent_data):
    """Fix tool names in agent definition to match Foundry pattern."""
    # Extract definition
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
    fixed_tools = []
    
    print(f"\nFixing {len(tools)} tools...")
    print("-" * 60)
    
    for i, tool in enumerate(tools):
        # Handle different tool structures
        if isinstance(tool, dict):
            # Check if it's the nested structure: {"type": "function", "function": {...}}
            if "function" in tool:
                tool_name = tool["function"].get("name", "")
                if tool_name:
                    sanitized_name = sanitize_tool_name(tool_name)
                    if sanitized_name != tool_name:
                        print(f"  Tool {i}: '{tool_name}' → '{sanitized_name}'")
                        tool["function"]["name"] = sanitized_name
                        updated_count += 1
                    else:
                        print(f"  Tool {i}: '{tool_name}' ✅")
                fixed_tools.append(tool)
            # Check if it's the flat structure: {"type": "function", "name": ...}
            elif "name" in tool:
                tool_name = tool.get("name", "")
                if tool_name:
                    sanitized_name = sanitize_tool_name(tool_name)
                    if sanitized_name != tool_name:
                        print(f"  Tool {i}: '{tool_name}' → '{sanitized_name}'")
                        tool["name"] = sanitized_name
                        updated_count += 1
                    else:
                        print(f"  Tool {i}: '{tool_name}' ✅")
                fixed_tools.append(tool)
            else:
                print(f"  Tool {i}: ⚠️  No name found, skipping")
                fixed_tools.append(tool)
        else:
            print(f"  Tool {i}: ⚠️  Unexpected format, skipping")
            fixed_tools.append(tool)
    
    # Update tools in definition
    definition["tools"] = fixed_tools
    
    print("-" * 60)
    if updated_count > 0:
        print(f"✅ Fixed {updated_count} tool names")
    else:
        print("✅ All tool names are valid")
    
    return updated_count > 0


def create_agent_version(token, agent_data):
    """Create a new agent version with fixed tool names."""
    endpoint = f"{ENDPOINT}/agents/{AGENT_NAME}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    # Extract definition
    if "versions" in agent_data and "latest" in agent_data["versions"]:
        definition = agent_data["versions"]["latest"]["definition"]
    elif "definition" in agent_data:
        definition = agent_data["definition"]
    else:
        print("❌ Agent definition not found")
        sys.exit(1)
    
    # Get current version number
    current_version = "1"
    if "versions" in agent_data and "latest" in agent_data["versions"]:
        current_version = str(agent_data["versions"]["latest"].get("version", "1"))
    
    # Increment version
    try:
        new_version = str(int(current_version) + 1)
    except ValueError:
        new_version = "2"
    
    # Create new version
    version_url = f"{endpoint}/versions"
    version_payload = {
        "version": new_version,
        "description": f"Fixed tool names to match Foundry pattern (^[a-zA-Z0-9_\\.-]+$)",
        "definition": definition,
    }
    
    print(f"\nCreating new agent version {new_version}...")
    try:
        response = requests.post(
            version_url,
            headers=headers,
            json=version_payload,
            params={"api-version": API_VERSION},
        )
        response.raise_for_status()
        version_data = response.json()
        print(f"✅ New agent version created: {version_data.get('version')}")
        return version_data
    except requests.exceptions.HTTPError as e:
        print(f"❌ Failed to create agent version: {e.response.status_code}")
        print(f"Response: {e.response.text}")
        raise


def main():
    """Main function."""
    print("=" * 60)
    print("Fix Elena Tool Names in Azure AI Foundry")
    print("=" * 60)
    print("")
    print(f"Endpoint: {ENDPOINT}")
    print(f"Agent: {AGENT_NAME}")
    print("")
    
    # Get access token
    print("Getting access token...")
    token = get_access_token()
    print("✅ Access token obtained")
    print("")
    
    # Get current agent
    print(f"Fetching agent '{AGENT_NAME}'...")
    endpoint = f"{ENDPOINT}/agents/{AGENT_NAME}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.get(
            endpoint,
            headers=headers,
            params={"api-version": API_VERSION},
        )
        response.raise_for_status()
        agent_data = response.json()
        print("✅ Agent fetched")
    except requests.exceptions.HTTPError as e:
        print(f"❌ Failed to fetch agent: {e.response.status_code}")
        print(f"Response: {e.response.text}")
        sys.exit(1)
    
    # Fix tool names
    has_changes = fix_tool_names(agent_data)
    
    if not has_changes:
        print("\n✅ No changes needed - all tool names are valid")
        return
    
    # Create new version with fixed tools
    try:
        create_agent_version(token, agent_data)
        print("\n✅ Tool names fixed successfully!")
    except Exception as e:
        print(f"\n❌ Failed to create new version: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

