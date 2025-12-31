# Documentation Reorganization Plan

## Current State Analysis

### Root Level Files (Too Many - Needs Organization)
- Core content: `index.md`, `architecture.md`, `agents.md`, `deployment.md`, `finops.md`
- Feature specs: `voice-chat-integration.md`, `connectors-plan.md`
- Guides: `TESTING-GUIDE.md`, `LOCAL-TESTING-GUIDE.md`, `setup-secrets-guide.md`
- Reports: `bug-fixing-progress-report.md`, `sage-visual-implementation-report.md`
- HTML duplicates: Many `.html` and `.old.html` files (should be removed or archived)

### Existing Folders (Good Structure)
- `architecture/` - Architecture docs and diagrams ✅
- `troubleshooting/` - Troubleshooting guides ✅
- `sop/` - Standard Operating Procedures ✅
- `dev-guides/` - Development guides ✅
- `concept/` - Conceptual documentation ✅
- `assets/` - Static assets ✅

### Issues Identified
1. **Too many root-level files** - Hard to navigate
2. **Duplicate content** - `.html` and `.md` versions
3. **Inconsistent naming** - Mix of kebab-case and UPPER_CASE
4. **Missing categories** - No clear "Getting Started", "Reference", etc.
5. **Scattered diagrams** - Some in root, some in architecture/, some in assets/

## Proposed New Structure

```
docs/
├── README.md                          # Main landing page
├── _config.yml                        # Jekyll config
├── getting-started/
│   ├── index.md                       # Getting started guide
│   ├── quick-start.md                  # Quick start guide
│   ├── local-setup.md                  # Local development setup
│   └── secrets-setup.md               # Secrets configuration
├── architecture/
│   ├── index.md                        # Architecture overview
│   ├── brain-spine/                    # Brain + Spine pattern
│   │   ├── index.md
│   │   └── brain-spine-story.md
│   ├── context-schema/                  # 4-Layer Context Schema
│   │   ├── index.md
│   │   ├── 4-layer-context-schema-story.md
│   │   └── security-context-enterprise-architecture.md
│   ├── authentication/                 # Authentication & Security
│   │   ├── index.md
│   │   ├── authentication-analysis.md
│   │   ├── authentication-architecture-evolution.md
│   │   ├── enterprise-auth-strategy.md
│   │   ├── entra-external-id.md
│   │   └── diagrams/
│   │       ├── auth-flow-diagram.json
│   │       ├── security-context-flow-diagram.json
│   │       └── *.png
│   └── diagrams/                       # Architecture diagrams
│       ├── 4-layer-context-schema-diagram.json
│       └── brain-spine-diagram.json
├── agents/
│   ├── index.md                        # Agents overview (from agents.md)
│   ├── elena/                          # Elena agent docs
│   │   └── persona.md
│   ├── marcus/                         # Marcus agent docs
│   │   └── persona.md
│   └── sage/                           # Sage agent docs
│       └── visual-implementation-report.md
├── features/
│   ├── index.md
│   ├── voice/                          # Voice features
│   │   ├── index.md
│   │   ├── voice-chat-integration.md
│   │   └── voicelive-v2-architecture.md
│   ├── memory/                         # Memory features
│   │   ├── index.md
│   │   ├── memory-architecture.md
│   │   ├── knowledge-graph-implementation.md
│   │   └── sessions-vs-episodes.md
│   ├── connectors/                     # Connectors
│   │   ├── index.md
│   │   └── connectors-plan.md
│   └── mobile/                         # Mobile features
│       ├── index.md
│       └── [mobile-feature-specs]
├── development/
│   ├── index.md
│   ├── setup/                          # Development setup
│   │   ├── local-testing.md
│   │   ├── test-in-separate-terminal.md
│   │   └── github-secrets.md
│   ├── guides/                         # Development guides
│   │   ├── commit-guidelines.md
│   │   ├── visual-development.md
│   │   └── UI_DESIGN_REFERENCE.md
│   └── testing/                        # Testing guides
│       ├── TESTING-GUIDE.md
│       └── LOCAL-TESTING-GUIDE.md
├── deployment/
│   ├── index.md                        # Deployment overview (from deployment.md)
│   ├── enterprise/                     # Enterprise deployment
│   │   ├── index.md
│   │   └── [dev-guides content]
│   ├── infrastructure/                 # Infrastructure guides
│   │   ├── azure-postgresql.md
│   │   ├── app-insights-guide.md
│   │   └── storage-strategy.md
│   └── finops/                         # FinOps
│       ├── index.md                    # From finops.md
│       └── finops-bau-implementation.md
├── operations/
│   ├── index.md
│   ├── monitoring/                     # Monitoring & observability
│   │   ├── vendor-monitoring.md
│   │   └── data-plane-tagging.md
│   ├── stability/                      # Stability guides
│   │   └── [stability content]
│   └── troubleshooting/                # Troubleshooting (keep existing)
│       └── [existing troubleshooting files]
├── reference/
│   ├── index.md
│   ├── sop/                            # Standard Operating Procedures
│   │   └── [existing sop files]
│   ├── api/                            # API reference
│   │   └── auth-api.md
│   └── sessions/                       # Session documentation
│       └── [sessions content]
├── guides/
│   ├── index.md
│   ├── enterprise-poc-guide.md
│   ├── project-tracking-setup.md
│   └── system-navigator.md
└── assets/                             # Keep existing structure
    ├── images/
    ├── diagrams/
    ├── css/
    └── js/
```

## Migration Plan

### Phase 1: Create New Structure
1. Create new folder structure
2. Create index.md files for each section

### Phase 2: Move Files
1. Move architecture files to subfolders
2. Move feature files to features/
3. Move development files to development/
4. Move deployment files to deployment/
5. Move reference files to reference/

### Phase 3: Update Links
1. Update all internal markdown links
2. Update _config.yml navigation
3. Update index.md quick links

### Phase 4: Cleanup
1. Remove duplicate .html files (or archive)
2. Remove .old.html files
3. Standardize file naming (kebab-case)

## File Mapping

### Getting Started
- `index.md` → `getting-started/index.md` (new content)
- `local-testing.md` → `getting-started/local-setup.md`
- `setup-secrets-guide.md` → `getting-started/secrets-setup.md`

### Architecture
- `architecture.md` → `architecture/index.md`
- `4-layer-context-schema-story.md` → `architecture/context-schema/4-layer-context-schema-story.md`
- `brain-spine-story.md` → `architecture/brain-spine/brain-spine-story.md`
- `architecture/security-context-enterprise-architecture.md` → Keep in `architecture/context-schema/`
- `architecture/authentication-*.md` → `architecture/authentication/`

### Agents
- `agents.md` → `agents/index.md`
- Split agent personas into subfolders

### Features
- `voice-chat-integration.md` → `features/voice/voice-chat-integration.md`
- `connectors-plan.md` → `features/connectors/connectors-plan.md`
- `concept/memory-architecture.md` → `features/memory/memory-architecture.md`
- `knowledge-graph-implementation.md` → `features/memory/knowledge-graph-implementation.md`

### Development
- `visual-development.md` → `development/guides/visual-development.md`
- `UI_DESIGN_REFERENCE.md` → `development/guides/UI_DESIGN_REFERENCE.md`
- `TESTING-GUIDE.md` → `development/testing/TESTING-GUIDE.md`
- `development/commit-guidelines.md` → `development/guides/commit-guidelines.md`

### Deployment
- `deployment.md` → `deployment/index.md`
- `finops.md` → `deployment/finops/index.md`
- `dev-guides/*` → `deployment/enterprise/`

### Operations
- `troubleshooting/*` → `operations/troubleshooting/` (keep structure)
- `stability/*` → `operations/stability/`
- `vendor-monitoring.md` → `operations/monitoring/vendor-monitoring.md`

### Reference
- `sop/*` → `reference/sop/` (keep structure)
- `sessions/*` → `reference/sessions/`

## Navigation Updates

### New _config.yml Navigation
```yaml
nav:
  - title: Home
    url: /
  - title: Getting Started
    url: /getting-started
  - title: Architecture
    url: /architecture
  - title: Agents
    url: /agents
  - title: Features
    url: /features
  - title: Development
    url: /development
  - title: Deployment
    url: /deployment
  - title: Operations
    url: /operations
  - title: Reference
    url: /reference
```

## Benefits

1. **Clear Hierarchy** - Logical grouping by purpose
2. **Easy Navigation** - Clear categories
3. **Scalable** - Easy to add new content
4. **Professional** - Enterprise-grade organization
5. **Maintainable** - Clear structure for contributors

