# Backend Scripts

This directory contains utility scripts for managing the Engram backend.

## seed_memory.py

Ingests the canonical Engram project history into the live Zep instance as
**real episodic memories**. These aren't mock data - they're the actual
conversation history that agents can reference.

### Usage

```bash
# From the repository root
cd backend
python -m scripts.seed_memory
```

### What it does

1. Creates Zep sessions for each historical episode
2. Adds messages as episodic memory
3. Applies metadata (topics, agent_id, summary)

### Episodes Included

| Session ID | Agent | Topics | Summary |
|------------|-------|--------|---------|
| `sess-arch-001` | Elena | Architecture, Schema, Zep | Initial 4-layer context schema design |
| `sess-fe-001` | Marcus | Frontend, React, UX | Visual Access interface implementation |
| `sess-debug-001` | Elena | DevOps, CI/CD, Testing | CI/CD pipeline debugging |
| `sess-infra-002` | Marcus/Elena | Infrastructure, Azure, Zep, Temporal | Zep/Temporal deployment fixes |
