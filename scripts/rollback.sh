#!/bin/bash
# Rollback Script for Engram
#
# Provides quick rollback capabilities for:
# - Git commits
# - Container App revisions
# - Database migrations
#
# NIST AI RMF: MANAGE 4.1 (Incident Response)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

usage() {
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  git <commit-hash>     Revert to a specific git commit"
    echo "  container <revision>  Roll back Azure Container App to revision"
    echo "  db <migration>        Roll back database to specific migration"
    echo "  status                Show current deployment status"
    echo ""
    echo "Examples:"
    echo "  $0 git HEAD~1         Revert last commit"
    echo "  $0 git abc1234        Revert to specific commit"
    echo "  $0 container 5        Roll back to revision 5"
    echo "  $0 db 001             Roll back to migration 001"
    echo "  $0 status"
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# =============================================================================
# GIT ROLLBACK
# =============================================================================

rollback_git() {
    local target=$1
    
    if [ -z "$target" ]; then
        log_error "Please specify a commit hash or reference"
        exit 1
    fi
    
    log_info "Current HEAD: $(git rev-parse HEAD)"
    log_info "Rolling back to: $target"
    
    # Verify the target exists
    if ! git rev-parse "$target" > /dev/null 2>&1; then
        log_error "Invalid commit reference: $target"
        exit 1
    fi
    
    # Show what will be reverted
    echo ""
    log_warn "The following commits will be reverted:"
    git log --oneline "$target"..HEAD
    echo ""
    
    read -p "Proceed with rollback? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Rollback cancelled"
        exit 0
    fi
    
    # Create revert commit
    git revert --no-commit "$target"..HEAD
    git commit -s -m "revert: Rollback to $target

Automated rollback via scripts/rollback.sh
Original HEAD: $(git rev-parse HEAD~1)"
    
    log_info "Rollback commit created. Push to apply:"
    echo "  git push origin main"
}

# =============================================================================
# CONTAINER APP ROLLBACK
# =============================================================================

rollback_container() {
    local revision=$1
    local app_name=${2:-"engram-api"}
    local rg=${AZURE_RESOURCE_GROUP:-"rg-engram-dev"}
    
    if [ -z "$revision" ]; then
        log_error "Please specify a revision number"
        log_info "Use '$0 status' to see available revisions"
        exit 1
    fi
    
    log_info "Rolling back $app_name to revision $revision in $rg"
    
    # List current revisions
    log_info "Current revisions:"
    az containerapp revision list \
        --name "$app_name" \
        --resource-group "$rg" \
        --output table
    
    read -p "Proceed with rollback? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Rollback cancelled"
        exit 0
    fi
    
    # Activate the old revision and deactivate current
    az containerapp revision activate \
        --name "$app_name" \
        --resource-group "$rg" \
        --revision "${app_name}--${revision}"
    
    log_info "Revision $revision activated"
    log_info "Update traffic routing to complete rollback"
}

# =============================================================================
# DATABASE ROLLBACK
# =============================================================================

rollback_db() {
    local target=$1
    
    if [ -z "$target" ]; then
        log_error "Please specify a migration identifier"
        exit 1
    fi
    
    log_info "Rolling back database to migration: $target"
    
    cd "$PROJECT_ROOT/backend"
    
    # Show current migration status
    log_info "Current migration status:"
    alembic current
    
    log_warn "This will modify the database schema"
    read -p "Proceed with database rollback? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Rollback cancelled"
        exit 0
    fi
    
    # Run downgrade
    alembic downgrade "$target"
    
    log_info "Database rolled back to: $target"
}

# =============================================================================
# STATUS
# =============================================================================

show_status() {
    echo "=============================================="
    echo "DEPLOYMENT STATUS"
    echo "=============================================="
    
    # Git status
    echo ""
    log_info "Git Status:"
    echo "  Current branch: $(git branch --show-current)"
    echo "  Current HEAD: $(git rev-parse --short HEAD)"
    echo "  Last 5 commits:"
    git log --oneline -5 | sed 's/^/    /'
    
    # Azure status (if logged in)
    if command -v az &> /dev/null && az account show &> /dev/null; then
        echo ""
        log_info "Azure Container Apps:"
        local rg=${AZURE_RESOURCE_GROUP:-"rg-engram-dev"}
        
        for app in engram-api engram-worker; do
            echo "  $app:"
            az containerapp show \
                --name "$app" \
                --resource-group "$rg" \
                --query "{revision:properties.latestRevisionName,status:properties.runningStatus}" \
                --output tsv 2>/dev/null | sed 's/^/    /' || echo "    Not found"
        done
    else
        log_warn "Azure CLI not logged in. Skipping container status."
    fi
    
    echo ""
    echo "=============================================="
}

# =============================================================================
# MAIN
# =============================================================================

case "${1:-}" in
    git)
        rollback_git "$2"
        ;;
    container)
        rollback_container "$2" "$3"
        ;;
    db)
        rollback_db "$2"
        ;;
    status)
        show_status
        ;;
    *)
        usage
        exit 1
        ;;
esac
