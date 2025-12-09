#!/bin/bash
# Quick test script for VoiceLive integration

set -e

echo "=========================================="
echo "VoiceLive Integration Test"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -d "backend" ]; then
    echo "Error: Run this script from the project root"
    exit 1
fi

echo "Step 1: Checking VoiceLive SDK installation..."
cd backend

if pip show azure-ai-voicelive &> /dev/null; then
    echo "✓ VoiceLive SDK is installed"
else
    echo "✗ VoiceLive SDK not installed"
    echo ""
    read -p "Install azure-ai-voicelive? (y/n): " INSTALL
    if [[ $INSTALL == "y" ]]; then
        pip install azure-ai-voicelive
        echo "✓ Installed"
    else
        echo "Install with: pip install azure-ai-voicelive"
        exit 1
    fi
fi

echo ""
echo "Step 2: Checking environment variables..."
if [ -f "../.env" ]; then
    echo "✓ .env file exists"
    source ../.env
else
    echo "⚠️  .env file not found"
    echo "Create .env with:"
    echo "  AZURE_AI_ENDPOINT=https://zimax.services.ai.azure.com"
    echo "  AZURE_AI_PROJECT_NAME=zimax"
    echo "  AZURE_OPENAI_KEY=your-key"
fi

echo ""
echo "Step 3: Testing Python imports..."
python3 << 'PYTHON_EOF'
import sys
import os

# Set minimal environment
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_USER", "postgres")
os.environ.setdefault("POSTGRES_PASSWORD", "password")
os.environ.setdefault("POSTGRES_DB", "engram")
os.environ.setdefault("ZEP_API_URL", "http://localhost:8000")
os.environ.setdefault("TEMPORAL_HOST", "localhost:7233")

try:
    from backend.voice.voicelive_service import voicelive_service
    print("✓ VoiceLive service imported")
    
    from backend.core import get_settings
    settings = get_settings()
    print(f"✓ Settings loaded")
    print(f"  - Endpoint: {settings.azure_ai_endpoint or 'Not set'}")
    print(f"  - Project: {settings.azure_ai_project_name or 'Not set'}")
    print(f"  - OpenAI Key: {'Set' if settings.azure_openai_key else 'Not set'}")
    
    # Test endpoint
    try:
        endpoint = voicelive_service.endpoint
        print(f"✓ Effective endpoint: {endpoint}")
    except Exception as e:
        print(f"✗ Endpoint error: {e}")
        sys.exit(1)
    
    # Test instructions
    elena_inst = voicelive_service.get_elena_instructions()
    marcus_inst = voicelive_service.get_marcus_instructions()
    print(f"✓ Elena instructions: {len(elena_inst)} chars")
    print(f"✓ Marcus instructions: {len(marcus_inst)} chars")
    
    print("")
    print("✓ All basic tests passed!")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("Make sure you're running from project root")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✓ Basic tests passed!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "  1. Start backend: uvicorn backend.api.main:app --reload"
    echo "  2. Test WebSocket: python3 scripts/test-voicelive.py --connection"
    echo "  3. Or use browser DevTools to connect to:"
    echo "     ws://localhost:8082/api/v1/voice/voicelive/test-session"
    echo ""
else
    echo ""
    echo "✗ Tests failed. Check errors above."
    exit 1
fi

