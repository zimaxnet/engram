#!/bin/bash
# Ask Marcus to create GitHub issues via curl
# This script attempts to call the API with proper authentication

set -euo pipefail

API_URL="${API_URL:-https://staging-env-api.gentleriver-dd0de193.eastus2.azurecontainerapps.io}"
SESSION_ID="stability-tasks-$(date +%s)"

echo "🤖 Asking Marcus to create GitHub issues for stability tasks"
echo "============================================================"
echo ""
echo "API URL: $API_URL"
echo "Session ID: $SESSION_ID"
echo ""

# Check if we have a token
if [ -z "${AUTH_TOKEN:-}" ]; then
    echo "⚠️  AUTH_TOKEN not set. Attempting to get token..."
    echo ""
    echo "Options:"
    echo "1. Get token from Azure CLI:"
    echo "   export AUTH_TOKEN=\$(az account get-access-token --scope \"api://94d50189-d4de-4b80-8804-2f3bf2e2d14f/.default\" --query accessToken -o tsv)"
    echo ""
    echo "2. Or use the frontend chat interface (recommended):"
    echo "   See: docs/stability/how-to-work-with-marcus.md"
    echo ""
    
    # Try to get token automatically
    if command -v az &> /dev/null; then
        echo "🔍 Attempting to get token from Azure CLI..."
        AUTH_TOKEN=$(az account get-access-token --scope "api://94d50189-d4de-4b80-8804-2f3bf2e2d14f/.default" --query accessToken -o tsv 2>/dev/null || echo "")
        
        if [ -z "$AUTH_TOKEN" ]; then
            echo "❌ Could not get token automatically"
            echo ""
            echo "💡 Please use the frontend chat interface instead:"
            echo "   1. Open Engram frontend"
            echo "   2. Select Marcus"
            echo "   3. Send the message from: docs/stability/how-to-work-with-marcus.md"
            exit 1
        else
            echo "✅ Got token from Azure CLI"
        fi
    else
        echo "❌ Azure CLI not found. Cannot get token automatically."
        echo ""
        echo "💡 Please use the frontend chat interface instead:"
        echo "   See: docs/stability/how-to-work-with-marcus.md"
        exit 1
    fi
fi

# Message to send to Marcus
MESSAGE="Marcus, I need you to create GitHub issues for the Enterprise Stability Improvement tasks.

**Context:**
- Stability analysis has been ingested into Zep memory (session: enterprise-stability-analysis-2025-12-30)
- We have a 4-phase improvement plan with 13 tasks
- Task structure is documented in: scripts/create-stability-github-tasks.md

**Your Task:**
Please create GitHub issues for all the stability improvement tasks. Start with Phase 1 tasks (1.1, 1.2, 1.3, 1.4) which are Critical/High priority.

**For each task, use create_github_issue with:**
- Title: Task number + name (e.g., \"Task 1.1: Health Check Endpoints\")
- Body: Description + acceptance criteria from the task list
- Labels: As specified (e.g., \"stability\", \"phase-1\", \"health-checks\", \"backend\")
- Project: Add to \"Enterprise Stability Improvements\" project (create if needed)

**Phase 1 Tasks to Create:**
1. Task 1.1: Health Check Endpoints (Critical, Backend)
2. Task 1.2: Configuration Validation on Startup (Critical, Backend)
3. Task 1.3: Graceful Degradation for Zep Memory (High, Memory)
4. Task 1.4: Error Tracking and Logging (High, Error Handling)

**Reference:**
- Search Zep memory for \"enterprise stability analysis\" or \"stability improvement\"
- Task details: scripts/create-stability-github-tasks.md
- Full analysis: docs/stability/enterprise-stability-analysis.md

Please start by creating the Phase 1 tasks. After those are created, I'll ask you to create Phase 2-4 tasks."

echo "📝 Sending message to Marcus..."
echo ""

# Create JSON payload
JSON_PAYLOAD=$(jq -n \
  --arg content "$MESSAGE" \
  --arg agent_id "marcus" \
  --arg session_id "$SESSION_ID" \
  '{content: $content, agent_id: $agent_id, session_id: $session_id}')

# Send request
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_URL}/api/v1/chat" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$JSON_PAYLOAD")

# Extract HTTP code and body
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

echo "📡 Response Status: $HTTP_CODE"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Marcus Response:"
    echo "============================================================"
    echo "$BODY" | jq -r '.content' 2>/dev/null || echo "$BODY"
    echo "============================================================"
    echo ""
    echo "📊 Metadata:"
    echo "$BODY" | jq -r 'if .agent_name then "   Agent: \(.agent_name)" else empty end' 2>/dev/null
    echo "$BODY" | jq -r 'if .message_id then "   Message ID: \(.message_id)" else empty end' 2>/dev/null
    echo "$BODY" | jq -r 'if .session_id then "   Session ID: \(.session_id)" else empty end' 2>/dev/null
    echo "$BODY" | jq -r 'if .tokens_used then "   Tokens Used: \(.tokens_used)" else empty end' 2>/dev/null
    echo "$BODY" | jq -r 'if .latency_ms then "   Latency: \(.latency_ms | tostring | split(".")[0])ms" else empty end' 2>/dev/null
    echo ""
    echo "✅ Message sent successfully!"
    echo ""
    echo "📋 Next Steps:"
    echo "   1. Check Marcus's response above"
    echo "   2. Verify GitHub issues were created"
    echo "   3. If Phase 1 tasks are created, ask Marcus to create Phase 2-4"
    echo ""
    echo "💬 To continue, run:"
    echo "   ./scripts/ask-marcus-via-curl.sh"
    echo "   (or send a new message via frontend)"
else
    echo "❌ Request failed"
    echo ""
    echo "Response:"
    echo "$BODY" | head -20
    echo ""
    if [ "$HTTP_CODE" = "401" ]; then
        echo "💡 Authentication failed. Options:"
        echo "   1. Get a new token:"
        echo "      export AUTH_TOKEN=\$(az account get-access-token --scope \"api://94d50189-d4de-4b80-8804-2f3bf2e2d14f/.default\" --query accessToken -o tsv)"
        echo "   2. Use the frontend chat interface (recommended):"
        echo "      See: docs/stability/how-to-work-with-marcus.md"
    fi
    exit 1
fi

