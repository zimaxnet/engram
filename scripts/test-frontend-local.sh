#!/bin/bash
# Quick script to test frontend locally

set -e

cd "$(dirname "$0")/../frontend"

echo "🔧 Setting up frontend for local testing..."
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Set API URL to deployed backend
export VITE_API_URL=https://engram-api.calmgrass-018b2019.eastus2.azurecontainerapps.io

echo "✅ API URL set to: $VITE_API_URL"
echo ""
echo "🚀 Starting dev server..."
echo "   Open http://localhost:5173 in your browser"
echo "   Press Ctrl+C to stop"
echo ""

npm run dev

