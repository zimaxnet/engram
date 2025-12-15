# Development Scratchpad

This folder contains working files for incremental development of the Engram platform.

## Structure

```
.dev/
├── test-suites/  # All test files organized by type
│   ├── unit/        # Unit tests (Python)
│   ├── integration/ # Integration tests
│   ├── e2e/         # End-to-end tests (Playwright)
│   ├── staging/     # Staging environment tests
│   └── reports/     # Test execution reports
├── scratch/      # Working files, experiments, temp code
├── spikes/       # Technical spikes and prototypes  
└── notes/        # Development notes and decisions
```

## Guidelines

- **test-suites/** - All test development happens here. Organized by test type.
- **scratch/** - Throwaway code for testing ideas. Delete when done.
- **spikes/** - Named prototypes (e.g., `spike-azure-speech/`). Keep for reference.
- **notes/** - Markdown files documenting decisions, learnings, blockers.

## Current Phase

**Phase 1: Foundation** (Weeks 1-3)
- [x] Scratchpad structure
- [ ] Azure Key Vault integration
- [ ] Backend project structure
- [ ] 4-layer Context Schema
- [ ] Microsoft Entra ID auth
- [ ] Frontend 3-column layout

## Notes Convention

Use format: `YYYY-MM-DD-topic.md` (e.g., `2025-12-08-keyvault-setup.md`)

