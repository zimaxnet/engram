#!/bin/bash
# Documentation Reorganization Script
# This script reorganizes the docs folder into a logical structure

set -e

echo "📚 Starting documentation reorganization..."

# Create new directory structure
echo "Creating new directory structure..."
mkdir -p getting-started
mkdir -p architecture/brain-spine
mkdir -p architecture/context-schema
mkdir -p architecture/authentication/diagrams
mkdir -p agents/elena
mkdir -p agents/marcus
mkdir -p agents/sage
mkdir -p features/voice
mkdir -p features/memory
mkdir -p features/connectors
mkdir -p features/mobile
mkdir -p development/setup
mkdir -p development/guides
mkdir -p development/testing
mkdir -p deployment/enterprise
mkdir -p deployment/infrastructure
mkdir -p deployment/finops
mkdir -p operations/monitoring
mkdir -p operations/stability
mkdir -p reference/api
mkdir -p reference/sessions
mkdir -p guides

echo "✅ Directory structure created"

# Move architecture files
echo "Moving architecture files..."
mv 4-layer-context-schema-story.md architecture/context-schema/ 2>/dev/null || true
mv brain-spine-story.md architecture/brain-spine/ 2>/dev/null || true
mv architecture/security-context-enterprise-architecture.md architecture/context-schema/ 2>/dev/null || true
mv architecture/authentication-*.md architecture/authentication/ 2>/dev/null || true
mv architecture/enterprise-auth-strategy.md architecture/authentication/ 2>/dev/null || true
mv architecture/entra-external-id.md architecture/authentication/ 2>/dev/null || true
mv architecture/auth-*.json architecture/authentication/diagrams/ 2>/dev/null || true
mv architecture/security-context-flow-diagram.json architecture/authentication/diagrams/ 2>/dev/null || true
mv architecture/*.png architecture/authentication/diagrams/ 2>/dev/null || true

# Move feature files
echo "Moving feature files..."
mv voice-chat-integration.md features/voice/ 2>/dev/null || true
mv connectors-plan.md features/connectors/ 2>/dev/null || true
mv concept/memory-architecture.md features/memory/ 2>/dev/null || true
mv concept/sessions-vs-episodes.md features/memory/ 2>/dev/null || true
mv knowledge-graph-implementation.md features/memory/ 2>/dev/null || true
mv mobile-feature-specs/* features/mobile/ 2>/dev/null || true
mv diagrams/voicelive-v2-architecture.md features/voice/ 2>/dev/null || true

# Move development files
echo "Moving development files..."
mv local-testing.md development/setup/ 2>/dev/null || true
mv test-in-separate-terminal.md development/setup/ 2>/dev/null || true
mv github-secrets.md development/setup/ 2>/dev/null || true
mv setup-secrets-guide.md getting-started/secrets-setup.md 2>/dev/null || true
mv visual-development.md development/guides/ 2>/dev/null || true
mv UI_DESIGN_REFERENCE.md development/guides/ 2>/dev/null || true
mv development/commit-guidelines.md development/guides/ 2>/dev/null || true
mv TESTING-GUIDE.md development/testing/ 2>/dev/null || true
mv LOCAL-TESTING-GUIDE.md development/testing/ 2>/dev/null || true

# Move deployment files
echo "Moving deployment files..."
mv finops.md deployment/finops/index.md 2>/dev/null || true
mv finops-bau-implementation.md deployment/finops/ 2>/dev/null || true
mv azure-postgresql.md deployment/infrastructure/ 2>/dev/null || true
mv app-insights-guide.md deployment/infrastructure/ 2>/dev/null || true
mv storage-strategy.md deployment/infrastructure/ 2>/dev/null || true
mv dev-guides/* deployment/enterprise/ 2>/dev/null || true

# Move operations files
echo "Moving operations files..."
mv stability/* operations/stability/ 2>/dev/null || true
mv vendor-monitoring.md operations/monitoring/ 2>/dev/null || true
mv data-plane-tagging.md operations/monitoring/ 2>/dev/null || true

# Move reference files
echo "Moving reference files..."
mv sessions/* reference/sessions/ 2>/dev/null || true
mv sop/auth-api.md reference/api/ 2>/dev/null || true

# Move guide files
echo "Moving guide files..."
mv enterprise_poc_guide.md guides/enterprise-poc-guide.md 2>/dev/null || true
mv Project-Tracking-Setup.md guides/project-tracking-setup.md 2>/dev/null || true
mv system-navigator.md guides/ 2>/dev/null || true

# Move diagram JSON files to architecture
echo "Moving diagram files..."
mv 4-layer-context-schema-diagram.json architecture/context-schema/ 2>/dev/null || true
mv brain-spine-diagram.json architecture/brain-spine/ 2>/dev/null || true
mv knowledge_graph.json architecture/context-schema/ 2>/dev/null || true

echo "✅ File reorganization complete"
echo ""
echo "📝 Next steps:"
echo "1. Create index.md files for each section"
echo "2. Update internal links"
echo "3. Update _config.yml navigation"
echo "4. Remove duplicate .html files"

