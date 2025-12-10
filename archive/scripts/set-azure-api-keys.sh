#!/bin/bash
# Set Azure OpenAI and Speech API keys in GitHub Secrets

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

# Azure OpenAI Key
echo "Azure OpenAI API Key"
echo "Get it from: Azure Portal → Your OpenAI resource → Keys and Endpoint"
read -sp "Enter Azure OpenAI API key (or press Enter to skip): " OPENAI_KEY
echo ""

if [ -n "$OPENAI_KEY" ]; then
    echo "$OPENAI_KEY" | gh secret set AZURE_OPENAI_KEY
    echo "✓ AZURE_OPENAI_KEY set successfully"
else
    echo "Skipped AZURE_OPENAI_KEY"
fi

echo ""

# Azure Speech Key
echo "Azure Speech Services API Key"
echo "Get it from: Azure Portal → Your Speech resource → Keys and Endpoint"
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
echo "To verify secrets were set correctly:"
echo "  gh secret list"
echo ""

