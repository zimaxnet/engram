#!/bin/bash
# Verify Deployment Status
# Checks if latest code is deployed

set -e

echo "🚀 Verifying Deployment"
echo "======================"

# Check latest commit
echo ""
echo "1. Latest commit:"
git log -1 --oneline

# Check GitHub Actions status
echo ""
echo "2. GitHub Actions deployment status:"
if command -v gh &> /dev/null; then
    gh run list --limit 1 --json status,conclusion,createdAt,headBranch \
      --jq '.[] | "   Status: \(.status)\n   Conclusion: \(.conclusion // "N/A")\n   Created: \(.createdAt)\n   Branch: \(.headBranch)"' 2>&1 || echo "   GitHub CLI not configured"
else
    echo "   GitHub CLI not available"
fi

# Check container revision
echo ""
echo "3. Active container revision:"
az containerapp revision list --name staging-env-api --resource-group engram-rg \
  --query "[0].{name:name, createdTime:properties.createdTime, active:properties.active, trafficWeight:properties.trafficWeight}" \
  --output json

# Check if new code is running
echo ""
echo "4. Checking for new code indicators in logs:"
az containerapp logs show --name staging-env-api --resource-group engram-rg \
  --tail 100 --type console 2>&1 | grep -iE "🔐|Auth module loaded|conditional" | tail -5 || echo "   No new code indicators found"

echo ""
echo "✅ Deployment check complete"

