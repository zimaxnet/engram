#!/bin/bash
# Setup GitHub Projects for Production-Grade System Implementation Plan
# This script creates a GitHub Project and sets up the initial structure

set -e

echo "🚀 Setting up GitHub Projects for Production-Grade System Implementation"
echo ""

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed"
    echo "   Install from: https://cli.github.com/"
    exit 1
fi

# Check authentication
if ! gh auth status &> /dev/null; then
    echo "❌ Not authenticated with GitHub"
    echo "   Run: gh auth login"
    exit 1
fi

# Get repository info
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
echo "📦 Repository: $REPO"
echo ""

# Check if project scope is available
echo "🔐 Checking GitHub Projects permissions..."
if ! gh auth refresh -s read:project,write:project 2>/dev/null; then
    echo "⚠️  Note: You may need to authorize GitHub Projects access"
    echo "   Run: gh auth refresh -s read:project,write:project"
fi
echo ""

# Create project
PROJECT_NAME="Production-Grade System Implementation"
PROJECT_DESCRIPTION="Implementation plan for all 7 layers of production-grade agentic systems"

echo "📋 Creating GitHub Project: $PROJECT_NAME"
PROJECT_ID=$(gh project create --title "$PROJECT_NAME" --body "$PROJECT_DESCRIPTION" --format json | jq -r '.id')

if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "null" ]; then
    echo "❌ Failed to create project"
    exit 1
fi

echo "✅ Project created: $PROJECT_ID"
echo ""

# Create fields (custom fields for task tracking)
echo "📊 Setting up project fields..."

# Status field (Todo, In Progress, Done)
gh project field-create "$PROJECT_ID" --name "Status" --single-select-option "Todo" --single-select-option "In Progress" --single-select-option "Done" 2>/dev/null || echo "⚠️  Status field may already exist"

# Priority field
gh project field-create "$PROJECT_ID" --name "Priority" --single-select-option "Critical" --single-select-option "High" --single-select-option "Medium" --single-select-option "Low" 2>/dev/null || echo "⚠️  Priority field may already exist"

# Owner field (for Elena/Marcus assignment)
gh project field-create "$PROJECT_ID" --name "Owner" --single-select-option "Elena (Business Analyst)" --single-select-option "Marcus (Project Manager)" --single-select-option "Sage (Storyteller)" 2>/dev/null || echo "⚠️  Owner field may already exist"

# Phase field
gh project field-create "$PROJECT_ID" --name "Phase" --single-select-option "Phase 1: Critical Security" --single-select-option "Phase 2: Production Reliability" --single-select-option "Phase 3: Advanced Capabilities" --single-select-option "Phase 4: Enterprise Polish" 2>/dev/null || echo "⚠️  Phase field may already exist"

# Layer field
gh project field-create "$PROJECT_ID" --name "Layer" --single-select-option "Layer 1: Interaction" --single-select-option "Layer 2: Orchestration" --single-select-option "Layer 3: Cognition" --single-select-option "Layer 4: Memory" --single-select-option "Layer 5: Tools" --single-select-option "Layer 6: Guardrails" --single-select-option "Layer 7: Observability" 2>/dev/null || echo "⚠️  Layer field may already exist"

echo "✅ Project fields configured"
echo ""

# Create views
echo "📑 Creating project views..."

# Create "By Phase" view
gh project view-create "$PROJECT_ID" --name "By Phase" --query "phase:Phase 1" 2>/dev/null || echo "⚠️  Views may need manual setup"

# Create "By Owner" view
gh project view-create "$PROJECT_ID" --name "By Owner" --query "owner:Elena" 2>/dev/null || echo "⚠️  Views may need manual setup"

echo "✅ Project views configured"
echo ""

# Output project URL
PROJECT_NUMBER=$(gh project view "$PROJECT_ID" --json number -q .number 2>/dev/null || echo "?")
echo "🎉 GitHub Project setup complete!"
echo ""
echo "📌 Project Details:"
echo "   ID: $PROJECT_ID"
echo "   Number: $PROJECT_NUMBER"
echo "   Name: $PROJECT_NAME"
echo ""
echo "🔗 View project:"
echo "   https://github.com/$REPO/projects/$PROJECT_NUMBER"
echo ""
echo "📝 Next steps:"
echo "   1. Review the project structure"
echo "   2. Import tasks from docs/Production-Grade-System-Implementation-Plan.md"
echo "   3. Assign owners (Elena/Marcus) to tasks"
echo "   4. Set up automation for task creation from plan"
echo ""

