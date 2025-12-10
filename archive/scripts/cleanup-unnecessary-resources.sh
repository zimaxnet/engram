#!/bin/bash
# Cleanup unnecessary resources in engram-rg to minimize costs

set -e

RESOURCE_GROUP="engram-rg"

echo "🔍 Resource Cleanup for $RESOURCE_GROUP"
echo "========================================"
echo ""

# 1. Remove Zep Container App (using Zep Cloud now)
echo "1️⃣  Removing Zep container app (using Zep Cloud)..."
if az containerapp show --name zep --resource-group $RESOURCE_GROUP &>/dev/null; then
    echo "   Found Zep container app"
    read -p "   Remove Zep container app? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        az containerapp delete \
            --name zep \
            --resource-group $RESOURCE_GROUP \
            --yes
        echo "   ✅ Zep container app removed"
    else
        echo "   ⏭️  Skipped"
    fi
else
    echo "   ℹ️  Zep container app not found (already removed?)"
fi
echo ""

# 2. Remove old OpenAI resource (replaced by v2)
echo "2️⃣  Removing old OpenAI resource (staging-env-openai)..."
if az cognitiveservices account show --name staging-env-openai --resource-group $RESOURCE_GROUP &>/dev/null; then
    echo "   Found old OpenAI resource"
    echo "   Active OpenAI: staging-env-openai-v2"
    read -p "   Remove old OpenAI resource? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        az cognitiveservices account delete \
            --name staging-env-openai \
            --resource-group $RESOURCE_GROUP \
            --yes
        echo "   ✅ Old OpenAI resource removed"
    else
        echo "   ⏭️  Skipped"
    fi
else
    echo "   ℹ️  Old OpenAI resource not found (already removed?)"
fi
echo ""

# 3. Review Storage Account
echo "3️⃣  Reviewing Storage Account (stagingenvstore)..."
if az storage account show --name stagingenvstore --resource-group $RESOURCE_GROUP &>/dev/null; then
    echo "   Found storage account: stagingenvstore"
    echo "   ⚠️  CAUTION: Verify this is not used by ETL pipeline before removing"
    echo "   Storage accounts are cheap (~$1-2/month) but should be removed if unused"
    read -p "   Remove storage account? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Check if it has containers/blobs
        CONTAINER_COUNT=$(az storage container list \
            --account-name stagingenvstore \
            --auth-mode login \
            --query "length(@)" -o tsv 2>/dev/null || echo "0")
        
        if [ "$CONTAINER_COUNT" -gt 0 ]; then
            echo "   ⚠️  WARNING: Storage account has $CONTAINER_COUNT container(s)"
            read -p "   Are you sure you want to delete? (yes/N): " -r
            echo
            if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
                az storage account delete \
                    --name stagingenvstore \
                    --resource-group $RESOURCE_GROUP \
                    --yes
                echo "   ✅ Storage account removed"
            else
                echo "   ⏭️  Skipped (has containers)"
            fi
        else
            az storage account delete \
                --name stagingenvstore \
                --resource-group $RESOURCE_GROUP \
                --yes
            echo "   ✅ Storage account removed (empty)"
        fi
    else
        echo "   ⏭️  Skipped"
    fi
else
    echo "   ℹ️  Storage account not found (already removed?)"
fi
echo ""

echo "✅ Cleanup complete!"
echo ""
echo "📊 Remaining resources:"
az resource list --resource-group $RESOURCE_GROUP --query "[].{Name:name, Type:type}" -o table

