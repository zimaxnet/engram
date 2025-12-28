#!/bin/bash
# Install pre-commit hook to prevent rapid commits
# This hook enforces 14-minute wait between commits (deployment time)

set -e

HOOK_FILE=".git/hooks/pre-commit"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Installing pre-commit hook to prevent rapid commits..."
echo ""

# Create hooks directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/.git/hooks"

# Copy hook file
cat > "$PROJECT_ROOT/$HOOK_FILE" << 'HOOK_EOF'
#!/bin/bash
# Pre-commit hook to prevent rapid commits
# Warns if committing too soon after last commit
# Deployments take ~14 minutes, so we should wait at least that long

LAST_COMMIT_TIME=$(git log -1 --format=%ct 2>/dev/null || echo "0")
CURRENT_TIME=$(date +%s)
TIME_DIFF=$((CURRENT_TIME - LAST_COMMIT_TIME))
MIN_DEPLOYMENT_TIME=840  # 14 minutes in seconds

# Check if last commit was recent
if [ "$TIME_DIFF" -lt "$MIN_DEPLOYMENT_TIME" ] && [ "$LAST_COMMIT_TIME" != "0" ]; then
    MINUTES_AGO=$((TIME_DIFF / 60))
    SECONDS_AGO=$((TIME_DIFF % 60))
    
    echo "⚠️  WARNING: Last commit was only ${MINUTES_AGO}m ${SECONDS_AGO}s ago!"
    echo "   Deployments take ~14 minutes. This will trigger multiple concurrent deployments."
    echo "   This causes resource waste, conflicts, and makes debugging impossible."
    echo ""
    echo "   Options:"
    echo "   1. Wait for deployment to complete (~$((MIN_DEPLOYMENT_TIME - TIME_DIFF)) more seconds)"
    echo "   2. Check deployment status: gh run list --limit 1"
    echo "   3. Batch all changes into a single commit instead"
    echo ""
    
    # Check if deployment is still in progress
    if command -v gh &> /dev/null; then
        DEPLOYMENT_STATUS=$(gh run list --limit 1 --json status,conclusion --jq '.[0].status' 2>/dev/null || echo "unknown")
        if [ "$DEPLOYMENT_STATUS" = "in_progress" ]; then
            echo "   ⚠️  DEPLOYMENT IS STILL IN PROGRESS!"
            echo "   Do NOT commit until it completes."
            echo ""
        fi
    fi
    
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Commit aborted. Please wait for deployment to complete or batch changes."
        exit 1
    fi
fi

exit 0
HOOK_EOF

# Make executable
chmod +x "$PROJECT_ROOT/$HOOK_FILE"

echo "✅ Pre-commit hook installed at $HOOK_FILE"
echo ""
echo "The hook will:"
echo "  - Warn if committing within 14 minutes of last commit"
echo "  - Check if deployment is still in progress"
echo "  - Require confirmation to proceed"
echo ""
echo "This prevents multiple concurrent deployments."

