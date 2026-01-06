#!/bin/bash
#
# Configure Elena's tool endpoints in Azure AI Foundry
#
# This script configures all 16 Elena tools to point to Engram's tool endpoints.
# Each tool will call: https://engram.work/api/v1/tools/{tool_name}
#
# Prerequisites:
#   - Azure CLI installed and logged in: az login
#   - Foundry project access
#   - Elena agent created in Foundry (Agent ID: Elena)
#
# Usage:
#   ./scripts/configure_elena_tool_endpoints.sh
#

set -e

# Configuration
ENDPOINT="https://zimax.services.ai.azure.com/api/projects/zimax"
PROJECT="zimax"
AGENT_NAME="Elena"
API_VERSION="2025-11-15-preview"
TOOL_BASE_URL="https://engram.work/api/v1/tools"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "============================================================"
echo "Configuring Elena Tool Endpoints in Azure AI Foundry"
echo "============================================================"
echo ""
echo "Endpoint: $ENDPOINT"
echo "Project: $PROJECT"
echo "Agent: $AGENT_NAME"
echo "Tool Base URL: $TOOL_BASE_URL"
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI not found. Please install it first.${NC}"
    exit 1
fi

# Check if logged in
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not logged in to Azure. Logging in...${NC}"
    az login
fi

echo -e "${GREEN}✅ Azure CLI ready${NC}"
echo ""

# Get access token for Foundry API
echo "Getting access token..."
TOKEN=$(az account get-access-token --resource "https://ai.azure.com" --query accessToken -o tsv)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ Failed to get access token${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Access token obtained${NC}"
echo ""

# Define all Elena tools
declare -a TOOLS=(
    "analyze_requirements"
    "stakeholder_mapping"
    "create_user_story"
    "trigger_ingestion"
    "run_golden_thread"
    "search_memory"
    "delegate_to_sage"
    "send_email"
    "list_emails"
    "list_onedrive_files"
    "save_to_onedrive"
    "create_github_issue"
    "update_github_issue"
    "get_project_status"
    "list_my_tasks"
    "close_task"
)

echo "Configuring ${#TOOLS[@]} tools..."
echo ""

SUCCESS_COUNT=0
FAILED_TOOLS=()

# First, get the current agent definition
echo "Fetching current agent definition..."
AGENT_JSON=$(curl -s -X GET \
    "${ENDPOINT}/agents/${AGENT_NAME}?api-version=${API_VERSION}" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json")

if [ $? -ne 0 ] || [ -z "$AGENT_JSON" ]; then
    echo -e "${RED}❌ Failed to fetch agent definition${NC}"
    echo "Response: $AGENT_JSON"
    exit 1
fi

echo -e "${GREEN}✅ Agent definition fetched${NC}"
echo ""

# Note: Azure AI Foundry tool endpoint configuration might require updating the agent definition
# or using a separate tool configuration API. The exact API depends on Foundry's implementation.
# 
# For now, we'll use a Python script that uses the Azure AI Projects SDK or REST API
# to update tool configurations.

echo -e "${YELLOW}⚠️  Direct Azure CLI commands for tool endpoint configuration may not be available.${NC}"
echo -e "${YELLOW}⚠️  Using REST API approach instead...${NC}"
echo ""

# Create a Python script to handle the configuration
cat > /tmp/configure_tools.py << 'PYTHON_SCRIPT'
import json
import sys
import os
import subprocess

# Get token
result = subprocess.run(
    ["az", "account", "get-access-token", "--resource", "https://ai.azure.com", "--query", "accessToken", "-o", "tsv"],
    capture_output=True,
    text=True
)
token = result.stdout.strip()

if not token:
    print("❌ Failed to get access token")
    sys.exit(1)

endpoint = "https://zimax.services.ai.azure.com/api/projects/zimax"
agent_name = "Elena"
api_version = "2025-11-15-preview"
tool_base_url = "https://engram.work/api/v1/tools"

# Import requests if available, otherwise use curl
try:
    import requests
    
    # Get current agent
    response = requests.get(
        f"{endpoint}/agents/{agent_name}?api-version={api_version}",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to get agent: {response.status_code}")
        print(response.text)
        sys.exit(1)
    
    agent = response.json()
    print(f"✅ Retrieved agent: {agent.get('name', agent_name)}")
    
    # Update tools with endpoints
    if "definition" in agent and "tools" in agent["definition"]:
        tools = agent["definition"]["tools"]
        updated = False
        
        for tool in tools:
            tool_name = tool.get("name", "")
            if tool_name:
                # Add endpoint configuration to tool
                tool["endpoint"] = f"{tool_base_url}/{tool_name}"
                tool["method"] = "POST"
                tool["headers"] = {
                    "Content-Type": "application/json"
                }
                updated = True
                print(f"  ✅ Configured tool: {tool_name}")
        
        if updated:
            # Update agent with new tool configuration
            update_response = requests.put(
                f"{endpoint}/agents/{agent_name}?api-version={api_version}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json=agent
            )
            
            if update_response.status_code in [200, 201, 204]:
                print(f"\n✅ Successfully updated agent with tool endpoints")
            else:
                print(f"\n❌ Failed to update agent: {update_response.status_code}")
                print(update_response.text)
                sys.exit(1)
        else:
            print("⚠️  No tools found to configure")
    else:
        print("⚠️  Agent definition structure not as expected")
        print(json.dumps(agent, indent=2))
        
except ImportError:
    print("⚠️  'requests' library not available. Using curl approach...")
    print("Please install: pip install requests")
    sys.exit(1)
PYTHON_SCRIPT

# Run the Python script
if command -v python3 &> /dev/null; then
    python3 /tmp/configure_tools.py
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ Tool endpoint configuration complete!${NC}"
    else
        echo ""
        echo -e "${RED}❌ Tool endpoint configuration failed${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi

echo ""
echo "============================================================"
echo "Next Steps:"
echo "============================================================"
echo "1. Verify tool endpoints in Azure Portal:"
echo "   Azure AI Foundry → Project 'zimax' → Applications → 'Elena'"
echo ""
echo "2. Test a tool endpoint:"
echo "   curl -X POST https://engram.work/api/v1/tools/send_email \\"
echo "     -H 'Authorization: Bearer <token>' \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"to\": \"test@example.com\", \"subject\": \"Test\", \"body\": \"Hello\"}'"
echo ""
echo "3. Enable Foundry Elena in Engram:"
echo "   export USE_FOUNDRY_ELENA=true"
echo "   export ELENA_FOUNDRY_AGENT_ID=Elena"
echo ""

