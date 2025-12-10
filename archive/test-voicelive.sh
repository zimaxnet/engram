#!/bin/bash
# Test VoiceLive integration from project root

set -e

echo "=========================================="
echo "Testing VoiceLive Integration"
echo "=========================================="
echo ""

# Set environment variables
export AZURE_AI_ENDPOINT="https://zimax.services.ai.azure.com"
export AZURE_AI_PROJECT_NAME="zimax"
export AZURE_OPENAI_KEY="cf23c3ed0f9d420dbd02c1e95a5b5bb3"
export ENVIRONMENT="development"
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5432"
export POSTGRES_USER="postgres"
export POSTGRES_PASSWORD="password"
export POSTGRES_DB="engram"
export ZEP_API_URL="http://localhost:8000"
export TEMPORAL_HOST="localhost:7233"

# Run from project root
cd "$(dirname "$0")"

echo "Step 1: Checking Python environment..."

# Check if we're in a virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    echo "✓ Virtual environment detected: $VIRTUAL_ENV"
    PYTHON_CMD="$VIRTUAL_ENV/bin/python"
elif [ -d "venv" ]; then
    echo "⚠️  Virtual environment found but not activated"
    echo "   Activate it with: source venv/bin/activate"
    echo "   Or run: ./scripts/setup-venv.sh"
    echo ""
    read -p "Continue anyway? (y/n): " CONTINUE
    if [[ $CONTINUE != "y" ]]; then
        exit 1
    fi
    PYTHON_CMD="venv/bin/python"
else
    PYTHON_CMD=$(which python3 || which python)
    echo "Using system Python: $PYTHON_CMD"
    echo "⚠️  Consider using a virtual environment (./scripts/setup-venv.sh)"
fi

echo ""
echo "Step 2: Checking if dependencies are installed..."
if ! $PYTHON_CMD -c "import pydantic" 2>/dev/null; then
    echo "⚠️  Dependencies not found."
    echo ""
    echo "Options:"
    echo "  1. Create and use a virtual environment (recommended):"
    echo "     python3 -m venv venv"
    echo "     source venv/bin/activate"
    echo "     cd backend && pip install -r requirements.txt"
    echo ""
    echo "  2. Install with --user flag:"
    echo "     cd backend && pip install --user -r requirements.txt"
    echo ""
    echo "  3. Use existing virtual environment if you have one"
    echo ""
    read -p "Install with --user flag now? (y/n): " INSTALL_USER
    if [[ $INSTALL_USER == "y" ]]; then
        cd backend
        $PYTHON_CMD -m pip install --user -q -r requirements.txt
        cd ..
        echo "✓ Dependencies installed (user install)"
    else
        echo "Please install dependencies manually, then run this script again."
        exit 1
    fi
else
    echo "✓ Dependencies found"
fi

echo ""
echo "Step 3: Testing VoiceLive import..."
$PYTHON_CMD << 'PYTHON_EOF'
import sys
import os

# Add backend to path
sys.path.insert(0, 'backend')

try:
    from backend.voice.voicelive_service import voicelive_service
    print("✓ VoiceLive service imported")
    
    elena = voicelive_service.get_elena_instructions()
    marcus = voicelive_service.get_marcus_instructions()
    print(f"✓ Elena instructions: {len(elena)} chars")
    print(f"✓ Marcus instructions: {len(marcus)} chars")
    
    endpoint = voicelive_service.endpoint
    print(f"✓ Endpoint: {endpoint}")
    
    print("")
    print("✓ All tests passed!")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    if 'voicelive' in str(e).lower():
        print("   Run: pip install azure-ai-voicelive")
    else:
        print("   Run: cd backend && pip install -r requirements.txt")
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
    echo "✓ VoiceLive Integration Test Passed!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "  1. Start backend:"
    echo "     cd backend"
    echo "     uvicorn backend.api.main:app --reload"
    echo ""
    echo "  2. Test WebSocket (browser console):"
    echo "     const ws = new WebSocket('ws://localhost:8082/api/v1/voice/voicelive/test-123');"
    echo "     ws.onopen = () => ws.send(JSON.stringify({type: 'agent', agent_id: 'elena'}));"
    echo "     ws.onmessage = (e) => console.log(JSON.parse(e.data));"
    echo ""
fi

