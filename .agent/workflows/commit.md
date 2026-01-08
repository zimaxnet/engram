---
description: Commit and push changes with memory enrichment
---

# Commit Workflow with Memory Enrichment

**POLICY**: Before every commit, enrich Zep memory with the full work context so agents can reference it in future turns.

## Steps

1. Stage changes:

```bash
git add -A && git status
```

1. **Enrich memory with full context** (REQUIRED):

```bash
# Recommended: Use the robust enrichment script
./scripts/enrich-commit.sh
```

> [!NOTE]
> If you encounter authentication errors, you may need to log in to Azure once with the correct scope:
>
> ```bash
> az login --tenant "8838531d-55dd-4018-8341-77705f4845f4" --scope "api://317f549d-67bb-4f73-90a3-ac0ebf95a420/.default"
> ```

Alternatively, for manual API calls (not recommended):

```bash
./scripts/api-call.sh POST /api/v1/memory/enrich ...
```

Alternatively, use the enrichment script:

```bash
./scripts/enrich-commit.sh
```

1. Commit with descriptive message:
// turbo

```bash
git commit -m "type: Brief description"
```

1. Push to remote:
// turbo

```bash
git push
```

## Context to Capture

When enriching, include:

- **Commit message** - What was done
- **Files changed** - List of modified/new/deleted files
- **Key decisions** - Why certain approaches were chosen
- **Issues created/closed** - Any GitHub tracking items
- **Roadmap items affected** - Which periodic table elements were touched

## Example Enrichment

```json
{
  "text": "## Git Commit Context\n\n**Commit**: 8d0f6bade\n**Branch**: main\n**Message**: feat: Add AI Periodic Table integration\n\n### Changed Files\n- README.md - Added AI Periodic Table section\n- docs/ai-periodic-table-roadmap.md - Tree structure mapping\n\n### Elements Touched\n- Fc (Function Call): Added enrich-commit.sh\n- Rg (RAG): Verified automatic context injection",
  "session_id": "commit-8d0f6bade",
  "speaker": "assistant",
  "agent_id": "antigravity",
  "channel": "git"
}
```

## Why This Matters

This enables the **Rg (RAG) automatic context injection** feature:

- When Elena/Marcus/Sage search, commit context surfaces
- Work history is preserved across sessions
- Agents understand what was done and why
