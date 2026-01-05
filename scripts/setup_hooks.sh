#!/bin/bash
# Setup Engram Git Hooks
# Installs post-commit hook for automatic memory enrichment.

HOOKS_DIR=".git/hooks"
HOOK_FILE="$HOOKS_DIR/post-commit"
SCRIPT_PATH="$(pwd)/scripts/engram_cli.py"

echo "🔧 Installing Engram Git Hooks..."

if [ ! -d ".git" ]; then
    echo "❌ Error: Not a git repository. Run this from the root of your repo."
    exit 1
fi

# Ensure commands exist
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 could not be found."
    exit 1
fi

# Create hook
cat > "$HOOK_FILE" <<EOF
#!/bin/bash
# Engram Automatic Enrichment Hook
# Triggers on git commit to push context to memory.

# Run in background to not block the commit workflow
nohup python3 "$SCRIPT_PATH" enrich --source git-commit > /dev/null 2>&1 &
EOF

# Make executable
chmod +x "$HOOK_FILE"

echo "✅ Installed post-commit hook at $HOOK_FILE"
echo "   It will run 'engram_cli.py enrich' automatically after every commit."
