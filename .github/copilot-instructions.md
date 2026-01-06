# Engram — Copilot Instructions

## Project Vocabulary
- **Gk** means **Graph Knowledge** (Engram’s owned term). Avoid “context graph” wording.
- **Fc** means **Function Calls** (explicit API calls + timings users can inspect).

## Memory (Make IDEs/Agents Aware)
When you learn something important during dev, ensure it becomes retrievable:

- Prefer **server-side enrichment** (works even when Zep is read-only from local):
  - POST `https://engram.work/api/v1/memory/enrich`
  - Use `session_id` to group related learnings (e.g. `ide-element-tagging`).

- For querying memory (when context already exists), use the workspace scripts:
  - `python -m backend.scripts.query_memory --env azure -q "<query>"`

## Release Tags (16 Elements)
We use a lightweight tag scheme for the “16 elements” program:

- Immutable milestone tags: `element-<symbol>-vX.Y` (never move)
- Moving pointer tags: `element-<symbol>-latest` (can be force-updated)

Current Gk tags:
- `element-gk-v1.0`
- `element-gk-latest`

## Deployment/Commit Discipline
Deployments take ~14 minutes. Batch related work into a single commit and avoid rapid consecutive pushes.
