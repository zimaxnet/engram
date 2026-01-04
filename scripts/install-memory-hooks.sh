#!/bin/bash
# Install memory enrichment hooks for continuous learning
# This creates a post-commit hook that ingests commit context into the Memory Graph
#
# Usage:
#   ./scripts/install-memory-hooks.sh
#
# turbo-all

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

echo "🧠 Installing Memory Enrichment Hooks"
echo ""

# Ensure hooks directory exists
mkdir -p "$HOOKS_DIR"

# ============================================================================
# POST-COMMIT HOOK - Ingest commit context into Memory Graph
# ============================================================================
cat > "$HOOKS_DIR/post-commit" << 'HOOK_EOF'
#!/bin/bash
# Post-commit hook: Ingest commit context into Engram Memory Graph
# This enables AI agents to recall recent development context

# Configuration
ENGRAM_ROOT="$(git rev-parse --show-toplevel)"
PYTHON="${ENGRAM_ROOT}/.venv/bin/python"
INGEST_SCRIPT="backend.scripts.ingest_commit"

# Check if we should skip (set SKIP_MEMORY_INGEST=1 to disable)
if [ "$SKIP_MEMORY_INGEST" = "1" ]; then
    exit 0
fi

# Check if Python and script exist
if [ ! -f "$PYTHON" ]; then
    # Silently skip if venv not set up
    exit 0
fi

# Get commit info
COMMIT_SHA=$(git rev-parse HEAD)
COMMIT_MSG=$(git log -1 --pretty=%B)
COMMIT_AUTHOR=$(git log -1 --pretty=%an)
BRANCH=$(git rev-parse --abbrev-ref HEAD)
FILES_CHANGED=$(git diff-tree --no-commit-id --name-only -r HEAD | head -10 | tr '\n' ', ')

# Run ingestion in background (don't block commit flow)
(
    cd "$ENGRAM_ROOT"
    "$PYTHON" -m backend.scripts.ingest_commit \
        --sha "$COMMIT_SHA" \
        --message "$COMMIT_MSG" \
        --author "$COMMIT_AUTHOR" \
        --branch "$BRANCH" \
        --files "$FILES_CHANGED" \
        --env azure \
        2>/dev/null &
) &

exit 0
HOOK_EOF

chmod +x "$HOOKS_DIR/post-commit"
echo "✅ Installed: post-commit (memory ingestion)"

# ============================================================================
# PRESERVE EXISTING PRE-COMMIT HOOK
# ============================================================================
if [ -f "$HOOKS_DIR/pre-commit" ]; then
    echo "ℹ️  Existing pre-commit hook preserved"
else
    echo "ℹ️  No pre-commit hook found (optional)"
fi

echo ""
echo "🎉 Memory Enrichment Hooks Installed!"
echo ""
echo "How it works:"
echo "  - Every commit automatically ingests context to Azure Zep"
echo "  - AI agents can recall: 'What did I fix yesterday?'"
echo "  - Query with: python -m backend.scripts.query_memory --env azure -q 'recent commits'"
echo ""
echo "To disable temporarily:"
echo "  SKIP_MEMORY_INGEST=1 git commit -m 'my message'"
echo ""
echo "To uninstall:"
echo "  rm .git/hooks/post-commit"
