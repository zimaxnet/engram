#!/bin/bash
# Set Azure Speech Services and OpenAI secrets
# Note: This is for traditional Azure Speech Services, not VoiceLive

set -e

echo "=========================================="
echo "Setting Azure API Keys"
echo "=========================================="
echo ""

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI not installed. Install from: https://cli.github.com"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "Logging into GitHub..."
    gh auth login
fi

echo "NOTE: Our platform uses Azure Speech Services (traditional), not VoiceLive"
echo "If you have VoiceLive credentials, you may need to use Speech Services instead"
echo ""

# Azure OpenAI Key
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Azure OpenAI API Key"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Get it from: Azure Portal → Your OpenAI resource → Keys and Endpoint"
echo ""
read -sp "Enter Azure OpenAI API key (or press Enter to skip): " OPENAI_KEY
echo ""

if [ -n "$OPENAI_KEY" ]; then
    echo "$OPENAI_KEY" | gh secret set AZURE_OPENAI_KEY
    echo "✓ AZURE_OPENAI_KEY set successfully"
else
    echo "Skipped AZURE_OPENAI_KEY"
fi

echo ""

# Azure Speech Services Key
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Azure Speech Services API Key"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Get it from: Azure Portal → Your Speech Services resource → Keys and Endpoint"
echo "NOTE: This is different from VoiceLive - we need traditional Speech Services"
echo ""
read -sp "Enter Azure Speech Services API key (or press Enter to skip): " SPEECH_KEY
echo ""

if [ -n "$SPEECH_KEY" ]; then
    echo "$SPEECH_KEY" | gh secret set AZURE_SPEECH_KEY
    echo "✓ AZURE_SPEECH_KEY set successfully"
else
    echo "Skipped AZURE_SPEECH_KEY"
fi

echo ""
echo "=========================================="
echo "Verifying secrets..."
echo "=========================================="
gh secret list

echo ""
echo "✓ Setup complete!"
echo ""
echo "Current secrets:"
echo "  - AZURE_OPENAI_KEY: $([ -n "$OPENAI_KEY" ] && echo "✓ Set" || echo "✗ Not set")"
echo "  - AZURE_SPEECH_KEY: $([ -n "$SPEECH_KEY" ] && echo "✓ Set" || echo "✗ Not set")"
echo ""
echo "To verify all secrets:"
echo "  gh secret list"
echo ""

