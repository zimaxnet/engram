#!/bin/bash
# Wait for deployment to complete, then commit auth robustness improvements

set -e

echo "⏳ Waiting for deployment to complete..."
echo ""

# Wait for deployment to finish
while true; do
    STATUS=$(gh run list --limit 1 --json status --jq '.[0].status' 2>/dev/null || echo "unknown")
    CONCLUSION=$(gh run list --limit 1 --json conclusion --jq '.[0].conclusion // "N/A"' 2>/dev/null || echo "N/A")
    ELAPSED=$(gh run list --limit 1 --json createdAt --jq '((now - (.[0].createdAt | fromdateiso8601)) / 60) | floor' 2>/dev/null || echo "0")
    
    echo "$(date +%H:%M:%S) - Status: $STATUS, Conclusion: $CONCLUSION, Elapsed: ${ELAPSED}m"
    
    if [ "$STATUS" = "completed" ]; then
        echo ""
        echo "✅ Deployment completed! Committing auth robustness improvements..."
        echo ""
        
        cd "$(dirname "$0")/.."
        
        git add backend/api/middleware/auth.py backend/api/routers/health.py scripts/test-all-services-comprehensive.sh
        
        git commit -m "fix: Make auth bypass more robust for enterprise POC

- Enhanced AUTH_REQUIRED checking (env var first, then settings)
- Handle multiple string formats (false, 0, no, off)
- Better logging and diagnostics
- Added /health/auth-status endpoint
- Double-check in get_current_user for reliability

Addresses recurring 401 errors by making auth bypass more defensive." || {
            echo "❌ Commit failed - may need to resolve conflicts or check git status"
            exit 1
        }
        
        git push || {
            echo "❌ Push failed - check network or permissions"
            exit 1
        }
        
        echo ""
        echo "✅ Auth robustness improvements committed and pushed!"
        echo ""
        echo "Next deployment will include these fixes."
        exit 0
    fi
    
    if [ "$STATUS" != "in_progress" ] && [ "$STATUS" != "queued" ]; then
        echo "⚠️  Deployment status is $STATUS (not in_progress or queued)"
        echo "Proceeding with commit anyway..."
        break
    fi
    
    sleep 30
done

