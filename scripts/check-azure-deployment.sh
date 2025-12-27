#!/bin/bash
# Check and manage Azure deployment status

RESOURCE_GROUP="engram-rg"
DEPLOYMENT_NAME="engram-infra-3f42950c9fa8b4fedd194d44da5bb210877db4a6"

echo "=========================================="
echo "Azure Deployment Status Check"
echo "=========================================="
echo ""

# Check deployment status
echo "📊 Deployment Status:"
az deployment group show \
  --resource-group "$RESOURCE_GROUP" \
  --name "$DEPLOYMENT_NAME" \
  --query "{name:name, state:properties.provisioningState, timestamp:properties.timestamp, correlationId:properties.correlationId, duration:properties.duration}" \
  --output table

echo ""
echo "📋 Detailed Status:"
az deployment group show \
  --resource-group "$RESOURCE_GROUP" \
  --name "$DEPLOYMENT_NAME" \
  --query "properties.provisioningState" \
  --output tsv

echo ""
echo "=========================================="
echo "Options:"
echo "=========================================="
echo ""
echo "1. Wait for deployment to complete"
echo "   (Monitor with: az deployment group show --resource-group $RESOURCE_GROUP --name $DEPLOYMENT_NAME)"
echo ""
echo "2. Cancel the deployment:"
echo "   az deployment group cancel --resource-group $RESOURCE_GROUP --name $DEPLOYMENT_NAME"
echo ""
echo "3. Check for errors:"
echo "   az deployment group show --resource-group $RESOURCE_GROUP --name $DEPLOYMENT_NAME --query 'properties.error'"
echo ""

