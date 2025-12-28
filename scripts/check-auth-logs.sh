#!/bin/bash
# Check Auth-Related Logs
# Looks for auth module load, bypass messages, and 401 errors

set -e

echo "📋 Checking Auth-Related Logs"
echo "============================="

# Check for auth module load
echo ""
echo "1. Auth module load messages:"
az containerapp logs show --name staging-env-api --resource-group engram-rg \
  --tail 200 --type console 2>&1 | grep -iE "🔐|Auth module loaded|AUTH_REQUIRED" | tail -10 || echo "   No auth module load messages found"

# Check for auth bypass messages
echo ""
echo "2. Auth bypass messages:"
az containerapp logs show --name staging-env-api --resource-group engram-rg \
  --tail 200 --type console 2>&1 | grep -iE "✅|Auth bypass|poc-user" | tail -10 || echo "   No auth bypass messages found"

# Check for 401 errors
echo ""
echo "3. 401 Unauthorized errors:"
az containerapp logs show --name staging-env-api --resource-group engram-rg \
  --tail 200 --type console 2>&1 | grep -iE "401|unauthorized|Missing.*token" | tail -10 || echo "   No 401 errors found"

# Check recent requests
echo ""
echo "4. Recent API requests:"
az containerapp logs show --name staging-env-api --resource-group engram-rg \
  --tail 50 --type console 2>&1 | grep -iE "POST|GET.*/api/v1" | tail -10 || echo "   No recent API requests found"

echo ""
echo "✅ Log check complete"

