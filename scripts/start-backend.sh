#!/bin/bash
# Start the Engram backend server

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found"
    echo "Run: ./scripts/setup-venv.sh"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Set environment variables if not already set
export ENVIRONMENT="${ENVIRONMENT:-development}"
export POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
export POSTGRES_PORT="${POSTGRES_PORT:-5432}"
export POSTGRES_USER="${POSTGRES_USER:-postgres}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-password}"
export POSTGRES_DB="${POSTGRES_DB:-engram}"
export ZEP_API_URL="${ZEP_API_URL:-http://localhost:8000}"
export TEMPORAL_HOST="${TEMPORAL_HOST:-localhost:7233}"

# Load .env file if it exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo "Loading environment variables from .env file..."
    set -a  # Automatically export all variables
    source "$PROJECT_ROOT/.env"
    set +a
    echo "✓ .env loaded"
fi

# Set default Azure variables if not set
if [ -z "$AZURE_AI_ENDPOINT" ] && [ -z "$AZURE_VOICELIVE_ENDPOINT" ]; then
    export AZURE_AI_ENDPOINT="${AZURE_AI_ENDPOINT:-https://zimax.services.ai.azure.com}"
fi
if [ -z "$AZURE_AI_PROJECT_NAME" ] && [ -z "$AZURE_VOICELIVE_PROJECT_NAME" ]; then
    export AZURE_AI_PROJECT_NAME="${AZURE_AI_PROJECT_NAME:-zimax}"
fi
if [ -z "$AZURE_OPENAI_KEY" ]; then
    echo "⚠️  AZURE_OPENAI_KEY not set"
    echo ""
    echo "Set it with:"
    echo "  export AZURE_OPENAI_KEY=\"your-key-here\""
    echo "  Or add it to .env file"
    echo ""
    read -p "Continue anyway? (y/n): " CONTINUE
    if [[ $CONTINUE != "y" ]]; then
        exit 1
    fi
fi

echo "=========================================="
echo "Starting Engram Backend Server"
echo "=========================================="
echo ""
echo "Environment: $ENVIRONMENT"
echo "Backend will be available at: http://0.0.0.0:8082"
echo "API docs at: http://localhost:8082/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run from project root so Python can find 'backend' module
PYTHONPATH="$PROJECT_ROOT" uvicorn backend.api.main:app \
    --host 0.0.0.0 \
    --port 8082 \
    --reload \
    --reload-dir "$PROJECT_ROOT/backend" \
    --reload-exclude "venv/**" \
    --reload-exclude "*.pyc"

