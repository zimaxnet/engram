#!/bin/bash
# Enterprise Chat Deployment Validation Script
# Validates Model Router configuration for production readiness

set -e

echo "============================================================"
echo "Enterprise Chat Deployment Validation"
echo "============================================================"
echo ""
echo "This script validates the Model Router configuration for"
echo "enterprise deployment and customer presentation."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# Test 1: Environment Variables
echo "📋 Test 1: Environment Variables"
echo "-----------------------------------"

check_env_var() {
    local var_name=$1
    local var_value=$2
    local required=$3
    
    if [ -z "$var_value" ]; then
        if [ "$required" = "true" ]; then
            echo -e "${RED}❌ $var_name: NOT SET (REQUIRED)${NC}"
            ((ERRORS++))
        else
            echo -e "${YELLOW}⚠️  $var_name: NOT SET (OPTIONAL)${NC}"
            ((WARNINGS++))
        fi
    else
        # Mask sensitive values
        if [[ "$var_name" == *"KEY"* ]]; then
            masked_value="${var_value:0:8}...${var_value: -4}"
            echo -e "${GREEN}✅ $var_name: SET ($masked_value)${NC}"
        else
            echo -e "${GREEN}✅ $var_name: SET ($var_value)${NC}"
        fi
    fi
}

# Load environment variables (if .env exists)
if [ -f "backend/.env" ]; then
    export $(cat backend/.env | grep -v '^#' | xargs)
fi

# Check required variables
check_env_var "AZURE_AI_ENDPOINT" "$AZURE_AI_ENDPOINT" "true"
check_env_var "AZURE_AI_KEY" "$AZURE_AI_KEY" "true"
check_env_var "AZURE_AI_MODEL_ROUTER" "$AZURE_AI_MODEL_ROUTER" "true"
check_env_var "AZURE_AI_API_VERSION" "$AZURE_AI_API_VERSION" "false"

echo ""

# Test 2: Endpoint Format Validation
echo "🔍 Test 2: Endpoint Format Validation"
echo "-----------------------------------"

if [ -z "$AZURE_AI_ENDPOINT" ]; then
    echo -e "${RED}❌ Cannot validate endpoint format (AZURE_AI_ENDPOINT not set)${NC}"
    ((ERRORS++))
else
    if [[ "$AZURE_AI_ENDPOINT" == *"/openai/v1"* ]]; then
        echo -e "${GREEN}✅ Endpoint format: APIM Gateway (correct)${NC}"
        echo "   Endpoint: $AZURE_AI_ENDPOINT"
    elif [[ "$AZURE_AI_ENDPOINT" == *"services.ai.azure.com"* ]]; then
        echo -e "${YELLOW}⚠️  Endpoint format: Foundry Direct (use APIM Gateway for Model Router)${NC}"
        ((WARNINGS++))
    else
        echo -e "${RED}❌ Endpoint format: Unknown (expected APIM Gateway with /openai/v1)${NC}"
        ((ERRORS++))
    fi
fi

echo ""

# Test 3: Model Router Configuration
echo "📦 Test 3: Model Router Configuration"
echo "-----------------------------------"

if [ -z "$AZURE_AI_MODEL_ROUTER" ]; then
    echo -e "${RED}❌ AZURE_AI_MODEL_ROUTER not set - using direct deployment${NC}"
    echo "   This means Model Router is NOT being used"
    ((ERRORS++))
else
    echo -e "${GREEN}✅ Model Router configured: $AZURE_AI_MODEL_ROUTER${NC}"
fi

echo ""

# Test 4: API Connectivity Test
echo "🧪 Test 4: API Connectivity Test"
echo "-----------------------------------"

if [ -z "$AZURE_AI_ENDPOINT" ] || [ -z "$AZURE_AI_KEY" ]; then
    echo -e "${RED}❌ Cannot test API connectivity (missing endpoint or key)${NC}"
    ((ERRORS++))
else
    ENDPOINT=$(echo "$AZURE_AI_ENDPOINT" | sed 's|/$||')
    MODEL="${AZURE_AI_MODEL_ROUTER:-gpt-5.1-chat}"
    
    echo "   Testing: $ENDPOINT/chat/completions"
    echo "   Model: $MODEL"
    
    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$ENDPOINT/chat/completions" \
        -H "Ocp-Apim-Subscription-Key: $AZURE_AI_KEY" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"$MODEL\",
            \"messages\": [{\"role\": \"user\", \"content\": \"Hello, this is a connectivity test. Please respond with 'Test successful'.\"}]
        }" 2>&1)
    
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✅ API connectivity: SUCCESS (HTTP $HTTP_CODE)${NC}"
        CONTENT=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['choices'][0]['message']['content'][:50])" 2>/dev/null || echo "Response received")
        echo "   Response preview: $CONTENT..."
    else
        echo -e "${RED}❌ API connectivity: FAILED (HTTP $HTTP_CODE)${NC}"
        echo "   Response: $BODY"
        ((ERRORS++))
    fi
fi

echo ""

# Test 5: Configuration Consistency
echo "🔧 Test 5: Configuration Consistency"
echo "-----------------------------------"

if [ -n "$AZURE_AI_MODEL_ROUTER" ] && [[ "$AZURE_AI_ENDPOINT" != *"/openai/v1"* ]]; then
    echo -e "${YELLOW}⚠️  Model Router configured but endpoint is not APIM Gateway${NC}"
    echo "   Model Router works best with APIM Gateway"
    ((WARNINGS++))
fi

if [ -z "$AZURE_AI_MODEL_ROUTER" ] && [[ "$AZURE_AI_ENDPOINT" == *"/openai/v1"* ]]; then
    echo -e "${YELLOW}⚠️  APIM Gateway configured but Model Router not set${NC}"
    echo "   Consider setting AZURE_AI_MODEL_ROUTER=model-router for cost optimization"
    ((WARNINGS++))
fi

echo ""

# Summary
echo "============================================================"
echo "Validation Summary"
echo "============================================================"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED - Configuration is production-ready!${NC}"
    echo ""
    echo "Your Model Router configuration is validated and ready for:"
    echo "  ✅ Enterprise deployment"
    echo "  ✅ Customer presentation"
    echo "  ✅ Production use"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  TESTS PASSED WITH WARNINGS${NC}"
    echo "   Errors: $ERRORS"
    echo "   Warnings: $WARNINGS"
    echo ""
    echo "Configuration is functional but could be optimized."
    exit 0
else
    echo -e "${RED}❌ VALIDATION FAILED${NC}"
    echo "   Errors: $ERRORS"
    echo "   Warnings: $WARNINGS"
    echo ""
    echo "Please fix the errors above before deploying to production."
    exit 1
fi

