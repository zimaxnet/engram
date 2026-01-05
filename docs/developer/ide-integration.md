# IDE Integration: Memory Enrichment

> **"Don't just write code. write history."**

Engram's power lies in its **Self-Enriching Workflow**. Every debugging session, architectural decision, and "Aha!" moment should be captured in the system's memory, not just lost in temporary chat logs.

This guide helps you configure your IDE (Cursor, VS Code, Antigravity) to push context directly to Engram.

---

## 1. Integration by IDE

### Cursor

Cursor users don't need manual setup. The repository includes a rule file:
`[memory-enrich.mdc](file:///Users/derek/Library/CloudStorage/OneDrive-zimaxnet/code/engram/.cursor/rules/memory-enrich.mdc)`

Cursor will automatically detect this rule and provide the `enrich_memory` tool to the AI.

### Antigravity

Use the built-in slash command workflow:

- Command: `/enrich <text>`
- Source: `.agent/workflows/enrich.md`

Example:
> /enrich "We refactored the auth middleware to support Azure AD tokens"

### VS Code (Windsurf / Copilot)

You can add a **Task** to `.vscode/tasks.json` to run the enrichment script quickly.

**`.vscode/tasks.json`**:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Enrich Memory",
      "type": "shell",
      "command": "python3 scripts/enrich_from_ide.py --text \"${input:enrichText}\"",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always"
      }
    }
  ],
  "inputs": [
    {
      "id": "enrichText",
      "type": "promptString",
      "description": "What context do you want to save to memory?"
    }
  ]
}
```

### Manual Tool Definition (MCP)

If you are configuring a custom agent that requires the raw JSON schema:

```json
{
  "name": "enrich_memory",
  "description": "Push context, findings, or code explanations from the IDE directly to Engram's long-term memory. Use this to ensure the system remembers architectural decisions or debugging discoveries.",
  "parameters": {
    "type": "object",
    "properties": {
      "text": {
        "type": "string",
        "description": "The context, insight, or finding to store in memory."
      },
      "session_id": {
        "type": "string",
        "description": "Optional session ID to group related log entries (e.g., 'debugging-auth-bug')."
      },
      "speaker": {
        "type": "string",
        "enum": ["user", "assistant"],
        "description": "Who is generating this insight.",
        "default": "user"
      }
    },
    "required": ["text"]
  }
}
```

### Antigravity & VS Code (Windsurf/Copilot)

For tools that accept MCP (Model Context Protocol) or custom function calling definitions, use the schema above.

---

## 2. API Reference

If your IDE restricts custom tools, you can use the raw API via `curl` or our helper script.

**Endpoint:** `POST https://engram.work/api/v1/memory/enrich`

### Helper Script

We provide a Python script for easy usage:
`scripts/enrich_from_ide.py`

**Usage:**

```bash
# Set credentials (do this once in your profile)
export ENGRAM_API_TOKEN="your-token"

# Push an insight
python3 scripts/enrich_from_ide.py --text "We decided to use Imagen 3.0 because Nano Banana Pro provides better architectural alignment."
```

### Curl Command

```bash
curl -X POST "https://engram.work/api/v1/memory/enrich" \
  -H "Authorization: Bearer $ENGRAM_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The visual generation pipeline now strictly links Story -> Diagram -> Image",
    "session_id": "ide-context-updates"
  }'
```

---

## 3. Best Practices (Zero-Loss Development)

1. **Enrich on Success:** When you solve a hard bug, tell the agent: *"Enrich memory with the solution we just found."*
2. **Enrich on Decision:** When you choose Library A over Library B, tell the agent: *"Enrich memory with this architectural decision."*
3. **Tag Sessions:** Use consistent session IDs (e.g., `feature-voice-live`) so related memories are grouped together in the Knowledge Graph.
