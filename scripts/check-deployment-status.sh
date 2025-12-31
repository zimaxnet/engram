#!/bin/bash
#
# Check Deployment Status
#
# Shows current active deployment and recent deployment history
# Helps identify which deployment is currently active and if there are conflicts
#

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Deployment Status Check${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Get active revision
ACTIVE_REVISION=$(az containerapp show --name staging-env-api --resource-group engram-rg --query "properties.latestRevisionName" -o tsv 2>/dev/null)

if [ -z "$ACTIVE_REVISION" ]; then
    echo -e "${RED}❌ Could not get active revision${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Active Revision:${NC} $ACTIVE_REVISION"
echo ""

# Get revision details
REVISION_INFO=$(az containerapp revision show --name staging-env-api --resource-group engram-rg --revision "$ACTIVE_REVISION" --query "{createdTime:properties.createdTime, active:properties.active, trafficWeight:properties.trafficWeight, replicas:properties.replicas, healthState:properties.healthState, image:properties.template.containers[0].image}" -o json 2>/dev/null)

if [ -z "$REVISION_INFO" ]; then
    echo -e "${RED}❌ Could not get revision details${NC}"
    exit 1
fi

CREATED_TIME=$(echo "$REVISION_INFO" | jq -r '.createdTime')
TRAFFIC_WEIGHT=$(echo "$REVISION_INFO" | jq -r '.trafficWeight')
REPLICAS=$(echo "$REVISION_INFO" | jq -r '.replicas')
HEALTH=$(echo "$REVISION_INFO" | jq -r '.healthState')
IMAGE=$(echo "$REVISION_INFO" | jq -r '.image')

echo "   Created: $CREATED_TIME"
echo "   Traffic Weight: ${TRAFFIC_WEIGHT}%"
echo "   Replicas: $REPLICAS"
echo "   Health: $HEALTH"
echo "   Image: $IMAGE"
echo ""

# Check recent GitHub Actions deployments
echo -e "${BLUE}Recent GitHub Actions Deployments:${NC}"
gh run list --workflow=Deploy --limit 5 --json conclusion,status,createdAt,headSha,displayTitle --jq '.[] | "   \(.createdAt) | \(.status) | \(.conclusion // "N/A") | \(.headSha[0:7]) | \(.displayTitle)"' 2>/dev/null || echo "   Could not fetch GitHub Actions runs"
echo ""

# Check for multiple active revisions
echo -e "${BLUE}All Revisions:${NC}"
az containerapp revision list --name staging-env-api --resource-group engram-rg --query "[].{name:name, active:properties.active, createdTime:properties.createdTime, trafficWeight:properties.trafficWeight}" -o table 2>/dev/null
echo ""

# Check for conflicts
MULTIPLE_ACTIVE=$(az containerapp revision list --name staging-env-api --resource-group engram-rg --query "[?properties.active==\`true\`]" -o json 2>/dev/null | jq 'length')

if [ "$MULTIPLE_ACTIVE" -gt 1 ]; then
    echo -e "${YELLOW}⚠️  WARNING: Multiple active revisions detected!${NC}"
    echo "   This can cause traffic splitting and unpredictable behavior."
    echo ""
    echo "   To fix, set traffic to 100% on the desired revision:"
    echo "   az containerapp ingress traffic set \\"
    echo "     --name staging-env-api \\"
    echo "     --resource-group engram-rg \\"
    echo "     --revision-weight $ACTIVE_REVISION=100"
    echo ""
else
    echo -e "${GREEN}✅ Only one active revision (no conflicts)${NC}"
fi

# Check recent commits
echo ""
echo -e "${BLUE}Recent Commits:${NC}"
git log --oneline -5
echo ""

# Determine which commit the active revision likely corresponds to
echo -e "${BLUE}Analysis:${NC}"
echo "   Active revision created: $CREATED_TIME"
echo "   This revision likely corresponds to a commit deployed around that time."
echo ""
echo "   To find the exact commit, check GitHub Actions runs around:"
echo "   $(date -u -j -f "%Y-%m-%dT%H:%M:%S" "${CREATED_TIME%+*}" "+%Y-%m-%d %H:%M:%S UTC" 2>/dev/null || echo "$CREATED_TIME")"
echo ""

# Check for in-progress deployments
IN_PROGRESS=$(gh run list --workflow=Deploy --limit 1 --json status -q '.[0].status' 2>/dev/null || echo "unknown")

if [ "$IN_PROGRESS" = "in_progress" ]; then
    echo -e "${YELLOW}⚠️  Deployment currently in progress${NC}"
    echo "   Wait for it to complete before making new changes."
else
    echo -e "${GREEN}✅ No deployments currently in progress${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"

