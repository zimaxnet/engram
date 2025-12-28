#!/bin/bash
# Diagnose auth issue by checking logs and testing endpoint

echo "🔍 Diagnosing Auth Issue"
echo "========================"
echo ""

echo "1. Checking AUTH_REQUIRED environment variable:"
az containerapp show --name staging-env-api --resource-group engram-rg \
  --query "properties.template.containers[0].env[?name=='AUTH_REQUIRED']" \
  --output json

echo ""
echo "2. Checking recent auth-related logs:"
az containerapp logs show --name staging-env-api --resource-group engram-rg \
  --tail 100 --type console 2>&1 | grep -iE "(auth|AUTH_REQUIRED|bypass|401)" | tail -20

echo ""
echo "3. Testing endpoint with verbose output:"
curl -v -X POST "https://api.engram.work/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"model": "model-router", "messages": [{"role": "user", "content": "test"}], "session_id": "test-123"}' 2>&1 | grep -E "(HTTP|401|200|auth)" | head -10

