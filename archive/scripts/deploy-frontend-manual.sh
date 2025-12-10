#!/bin/bash
# Manual frontend deployment script

set -e

cd "$(dirname "$0")/.."

echo "🔧 Building frontend..."
cd frontend

# Get backend URL
BACKEND_URL=$(az containerapp show \
  --name engram-api \
  --resource-group engram-rg \
  --query "properties.configuration.ingress.fqdn" -o tsv)

export VITE_API_URL="https://${BACKEND_URL}"
echo "✅ Using API URL: $VITE_API_URL"

# Build
npm run build

echo ""
echo "📦 Build complete. Deploying to Static Web App..."

# Get deployment token
TOKEN=$(az staticwebapp secrets list \
  --name staging-env-web \
  --resource-group engram-rg \
  --query "properties.apiKey" -o tsv)

if [ -z "$TOKEN" ]; then
  echo "❌ Failed to get deployment token"
  exit 1
fi

echo "✅ Got deployment token"

# Deploy
cd dist
az staticwebapp deploy \
  --name staging-env-web \
  --resource-group engram-rg \
  --api-key "$TOKEN" \
  --source .

echo ""
echo "✅ Deployment complete!"
echo "🌐 Frontend should be available at: https://engram.work"
echo "   (May take a few minutes to propagate)"

