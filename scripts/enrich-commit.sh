#!/bin/bash
# Engram Commit Enrichment Script
#
# Automatically enriches Zep memory with commit context before pushing.
# This enables the "Automatic context injection at every turn" feature.
#
# Usage:
#   ./scripts/enrich-commit.sh "Your commit message"
#
# Or install as a pre-push hook:
#   cp scripts/enrich-commit.sh .git/hooks/pre-push
#   chmod +x .git/hooks/pre-push

set -e

COMMIT_MSG="${1:-$(git log -1 --pretty=%B)}"
BRANCH=$(git rev-parse --abbrev-ref HEAD)
COMMIT_HASH=$(git rev-parse --short HEAD)
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
SESSION_ID="commit-${COMMIT_HASH}-${TIMESTAMP}"

# Get staged files summary
STAGED_FILES=$(git diff --cached --name-only 2>/dev/null || git diff HEAD~1 --name-only 2>/dev/null || echo "No files")
FILES_CHANGED=$(echo "$STAGED_FILES" | wc -l | tr -d ' ')

# Get brief diff summary (first 1000 chars of stat)
DIFF_SUMMARY=$(git diff --cached --stat 2>/dev/null || git diff HEAD~1 --stat 2>/dev/null | head -20)

# Build enrichment payload
CONTEXT=$(cat <<EOF
## Git Commit Context

**Commit**: ${COMMIT_HASH}
**Branch**: ${BRANCH}
**Message**: ${COMMIT_MSG}
**Files Changed**: ${FILES_CHANGED}

### Changed Files
${STAGED_FILES}

### Diff Summary
\`\`\`
${DIFF_SUMMARY}
\`\`\`
EOF
)

echo "🧠 Enriching memory with commit context..."
echo "   Session: ${SESSION_ID}"
echo "   Files: ${FILES_CHANGED}"

# Get auth token
API_URL="${ENGRAM_API_URL:-https://api.engram.work}"

# Check if we have a token or need to get one
# Check if we have a token or need to get one
if [ -z "$ENGRAM_API_TOKEN" ]; then
    echo "   Getting Azure AD token..."
    # Capture both stdout and stderr
    # Default to staging app ID if not set
    RESOURCE_ID="${ENGRAM_API_RESOURCE:-api://317f549d-67bb-4f73-90a3-ac0ebf95a420}"
    if ! TOKEN_OUTPUT=$(az account get-access-token --resource "$RESOURCE_ID" --query accessToken -o tsv 2>&1); then
        echo "⚠️  Failed to acquire Azure token:"
        echo "$TOKEN_OUTPUT" | sed 's/^/   /'
        ENGRAM_API_TOKEN=""
    else
        ENGRAM_API_TOKEN="$TOKEN_OUTPUT"
    fi
fi

if [ -z "$ENGRAM_API_TOKEN" ]; then
    echo "⚠️  No auth token available. Skipping enrichment."
    echo "   Set ENGRAM_API_TOKEN or ensure 'az login' is configured."
    exit 0
fi

# Prepare JSON payload (escape special characters)
PAYLOAD=$(jq -n \
    --arg text "$CONTEXT" \
    --arg session_id "$SESSION_ID" \
    --arg speaker "assistant" \
    --arg agent_id "git-enricher" \
    --arg channel "git" \
    '{text: $text, session_id: $session_id, speaker: $speaker, agent_id: $agent_id, channel: $channel}')

# Call enrichment API
RESPONSE=$(curl -s -w "\n%{http_code}" \
    -X POST "${API_URL}/api/v1/memory/enrich" \
    -H "Authorization: Bearer ${ENGRAM_API_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD")

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Memory enriched successfully!"
    echo "   Session: $(echo "$BODY" | jq -r '.session_id // "unknown"')"
else
    echo "⚠️  Enrichment returned HTTP ${HTTP_CODE}"
    echo "   Response: $BODY"
fi
