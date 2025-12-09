#!/bin/bash
# Quick script to check if backend is running

echo "Checking backend status..."
echo ""

# Check if port is in use
if lsof -ti:8082 > /dev/null 2>&1; then
    echo "✓ Port 8082 is in use"
    echo ""
    
    # Try to connect
    if curl -s http://localhost:8082/health > /dev/null 2>&1; then
        echo "✓ Backend is responding!"
        echo ""
        echo "Health check:"
        curl -s http://localhost:8082/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8082/health
        echo ""
        echo "Ready to test VoiceLive!"
    else
        echo "⚠️  Port 8082 is in use but backend not responding"
        echo "   Backend may be starting up or crashed"
    fi
else
    echo "✗ Backend is NOT running"
    echo ""
    echo "Start it with:"
    echo "  ./scripts/start-backend.sh"
    echo ""
    echo "Or manually:"
    echo "  source venv/bin/activate"
    echo "  export AZURE_OPENAI_KEY=\"cf23c3ed0f9d420dbd02c1e95a5b5bb3\""
    echo "  PYTHONPATH=. uvicorn backend.api.main:app --host 0.0.0.0 --port 8082 --reload --reload-exclude \"venv/**\""
fi

