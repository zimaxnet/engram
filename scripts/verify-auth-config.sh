#!/bin/bash
# Verify Auth Configuration
# Checks AUTH_REQUIRED and related environment variables

set -e

echo "🔍 Verifying Auth Configuration"
echo "=============================="

# Check AUTH_REQUIRED setting
echo ""
echo "1. Checking AUTH_REQUIRED environment variable:"
AUTH_REQUIRED=$(az containerapp show --name staging-env-api --resource-group engram-rg \
  --query "properties.template.containers[0].env[?name=='AUTH_REQUIRED'].value" -o tsv 2>/dev/null || echo "NOT_SET")

if [ "$AUTH_REQUIRED" = "false" ] || [ "$AUTH_REQUIRED" = "False" ]; then
    echo "   ✅ AUTH_REQUIRED=false (correct for POC)"
elif [ "$AUTH_REQUIRED" = "true" ] || [ "$AUTH_REQUIRED" = "True" ]; then
    echo "   ⚠️  AUTH_REQUIRED=true (auth is enabled)"
else
    echo "   ❌ AUTH_REQUIRED=$AUTH_REQUIRED (unexpected value)"
fi

# Check ENVIRONMENT setting
echo ""
echo "2. Checking ENVIRONMENT variable:"
ENVIRONMENT=$(az containerapp show --name staging-env-api --resource-group engram-rg \
  --query "properties.template.containers[0].env[?name=='ENVIRONMENT'].value" -o tsv 2>/dev/null || echo "NOT_SET")
echo "   ENVIRONMENT=$ENVIRONMENT"

# Check if container is running
echo ""
echo "3. Checking container status:"
az containerapp show --name staging-env-api --resource-group engram-rg \
  --query "{name:name, status:properties.runningStatus, revision:properties.latestRevisionName}" \
  --output json

echo ""
echo "✅ Configuration check complete"

