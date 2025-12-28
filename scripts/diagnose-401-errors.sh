#!/bin/bash
# Complete Diagnostic for 401 Errors
# Runs all diagnostic steps and provides summary

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🔍 Complete Diagnostic for 401 Errors"
echo "======================================"
echo ""

# Run all diagnostic steps
echo "Step 1: Verifying Auth Configuration..."
bash "$SCRIPT_DIR/verify-auth-config.sh"

echo ""
echo "Step 2: Testing All Endpoints..."
bash "$SCRIPT_DIR/test-all-endpoints.sh"

echo ""
echo "Step 3: Checking Auth Logs..."
bash "$SCRIPT_DIR/check-auth-logs.sh"

echo ""
echo "Step 4: Verifying Deployment..."
bash "$SCRIPT_DIR/verify-deployment.sh"

echo ""
echo "📊 Diagnostic Summary"
echo "===================="
echo ""
echo "If all endpoints return 401:"
echo "  1. ✅ Verify AUTH_REQUIRED=false is set (Step 1)"
echo "  2. ✅ Check logs for '🔐 Auth module loaded' message (Step 3)"
echo "  3. ✅ Check logs for '✅ Auth bypass enabled' messages (Step 3)"
echo "  4. ✅ Verify latest code is deployed (Step 4)"
echo "  5. 🔄 Restart container if needed:"
echo "     az containerapp revision restart --name staging-env-api --resource-group engram-rg --revision <revision-name>"
echo ""
echo "Next Steps:"
echo "  - Review logs for specific error messages"
echo "  - Check if deployment completed successfully"
echo "  - Verify environment variables are set correctly"
echo "  - See docs/troubleshooting/chat-voice-episodes-401-errors.md for detailed troubleshooting"

