#!/bin/bash
# Simple VoiceLive test script

echo "=========================================="
echo "Testing VoiceLive Integration"
echo "=========================================="
echo ""

cd backend

echo "Step 1: Checking dependencies..."
if ! python3 -c "import pydantic" 2>/dev/null; then
    echo "⚠️  Installing dependencies..."
    pip install -r requirements.txt
fi

echo ""
echo "Step 2: Testing VoiceLive import..."
python3 << 'PYTHON'
import sys
import os
sys.path.insert(0, '.')

# Minimal environment
for k, v in {
    'ENVIRONMENT': 'development',
    'POSTGRES_HOST': 'localhost',
    'POSTGRES_PORT': '5432',
    'POSTGRES_USER': 'postgres',
    'POSTGRES_PASSWORD': 'password',
    'POSTGRES_DB': 'engram',
    'ZEP_API_URL': 'http://localhost:8000',
    'TEMPORAL_HOST': 'localhost:7233'
}.items():
    os.environ.setdefault(k, v)

try:
    from voice.voicelive_service import voicelive_service
    print("✓ VoiceLive service imported")
    
    elena = voicelive_service.get_elena_instructions()
    marcus = voicelive_service.get_marcus_instructions()
    print(f"✓ Elena instructions: {len(elena)} chars")
    print(f"✓ Marcus instructions: {len(marcus)} chars")
    
    try:
        endpoint = voicelive_service.endpoint
        print(f"✓ Endpoint: {endpoint}")
    except Exception as e:
        print(f"⚠️  Endpoint: {e}")
        print("   Set AZURE_AI_ENDPOINT and AZURE_AI_PROJECT_NAME")
    
    print("")
    print("✓ Test passed!")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    if 'voicelive' in str(e).lower():
        print("   Run: pip install azure-ai-voicelive")
    else:
        print("   Run: pip install -r requirements.txt")
    exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
PYTHON

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✓ Basic test passed!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "  1. Set environment variables:"
    echo "     export AZURE_AI_ENDPOINT='https://zimax.services.ai.azure.com'"
    echo "     export AZURE_AI_PROJECT_NAME='zimax'"
    echo "     export AZURE_OPENAI_KEY='your-key'"
    echo ""
    echo "  2. Start backend:"
    echo "     uvicorn backend.api.main:app --reload"
    echo ""
    echo "  3. Test WebSocket (browser console):"
    echo "     const ws = new WebSocket('ws://localhost:8082/api/v1/voice/voicelive/test-123');"
    echo "     ws.onopen = () => ws.send(JSON.stringify({type: 'agent', agent_id: 'elena'}));"
    echo "     ws.onmessage = (e) => console.log(JSON.parse(e.data));"
    echo ""
fi
