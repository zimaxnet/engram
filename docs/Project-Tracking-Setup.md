# Project Tracking Setup Guide

## Overview

This guide explains how to set up project tracking for the Production-Grade System Implementation Plan using GitHub Projects.

## GitHub Projects Setup

### Prerequisites

1. **GitHub CLI installed**
   ```bash
   # Check if installed
   gh --version
   
   # Install if needed (macOS)
   brew install gh
   ```

2. **Authenticated with GitHub**
   ```bash
   # Check authentication
   gh auth status
   
   # Login if needed
   gh auth login
   ```

3. **Project permissions**
   ```bash
   # Refresh auth with project scopes
   gh auth refresh -s read:project,write:project
   ```

### Automated Setup

Run the setup script:

```bash
chmod +x scripts/setup-github-projects.sh
./scripts/setup-github-projects.sh
```

This will:
- Create a new GitHub Project
- Set up custom fields (Status, Priority, Owner, Phase, Layer)
- Create initial views (By Phase, By Owner)
- Output the project URL

### Manual Setup

If automated setup doesn't work, follow these steps:

1. **Create Project**
   - Go to https://github.com/zimaxnet/engram
   - Click "Projects" tab
   - Click "New project"
   - Choose "Board" layout
   - Name: "Production-Grade System Implementation"

2. **Add Custom Fields**
   - Click "..." → "Customize fields"
   - Add fields:
     - **Status**: Single select (Todo, In Progress, Done)
     - **Priority**: Single select (Critical, High, Medium, Low)
     - **Owner**: Single select (Elena, Marcus, Sage)
     - **Phase**: Single select (Phase 1-4)
     - **Layer**: Single select (Layer 1-7)

3. **Create Views**
   - Click "..." → "New view"
   - Create views:
     - "By Phase" - Filter by Phase field
     - "By Owner" - Filter by Owner field
     - "By Layer" - Filter by Layer field
     - "Critical Tasks" - Filter Priority = Critical

## Task Owner Roles

### Elena (Business Analyst)
**Responsibilities:**
- Requirements analysis and documentation
- Input/output guardrails design
- Compliance mapping and documentation
- Context engineering and memory optimization
- Evaluation framework design

**Assigned Tasks:**
- Task 6.1: Input Guardrails Implementation
- Task 6.3: Output Guardrails
- Task 6.5: Compliance Mapping
- Task 3.2: Structured Output Enforcement
- Task 4.2: Context Optimization
- Task 7.2: Evaluation Framework

### Marcus (Project Manager)
**Responsibilities:**
- Project planning and timeline management
- Risk assessment and mitigation
- Execution guardrails (rate limiting, policies)
- Cost governance and budget tracking
- State management and orchestration
- Tool validation and sandboxing

**Assigned Tasks:**
- Task 6.2: Execution Guardrails
- Task 6.4: Circuit Breaker Pattern
- Task 3.1: LLM Gateway Implementation
- Task 7.3: Cost Governance
- Task 2.1: Enhanced Self-Correction
- Task 2.2: Hierarchical Agent Planning
- Task 2.3: State Persistence & Branching
- Task 5.1: Sandboxed Code Execution
- Task 5.2: Tool Validation Middleware

### Sage (Storyteller & Visualizer)
**Responsibilities:**
- Creating stories and visuals for documentation
- Generating architecture diagrams
- Creating visual timelines and project summaries
- Documenting implementation progress

**Delegation:**
- Both Elena and Marcus can delegate to Sage
- Elena delegates for: Requirements docs, compliance narratives, evaluation reports
- Marcus delegates for: Project timelines, risk visualizations, status reports, architecture diagrams

## Task Import Process

### Option 1: Manual Import

1. Open the implementation plan: `docs/Production-Grade-System-Implementation-Plan.md`
2. For each task (6.1, 6.2, etc.):
   - Create a new issue in GitHub
   - Title: Task number + name (e.g., "Task 6.1: Input Guardrails Implementation")
   - Body: Copy task description, sub-tasks, acceptance criteria
   - Labels: Add "production-grade-system", layer name, phase name
   - Assign: Set owner (Elena or Marcus)
   - Add to project: Add to "Production-Grade System Implementation" project
   - Set fields: Status (Todo), Priority, Phase, Layer

### Option 2: Automated Import (Future)

Create a script to parse the markdown and create issues automatically:

```python
# scripts/import-tasks-to-github.py
# Parse docs/Production-Grade-System-Implementation-Plan.md
# Create GitHub issues for each task
# Set fields and assign owners
```

## Workflow

### Daily Standup
- Review tasks by owner (Elena/Marcus)
- Check status of critical tasks (Layer 6)
- Identify blockers
- Update task status

### Weekly Review
- Review phase progress
- Assess risk and timeline
- Adjust priorities if needed
- Generate status report (Marcus)

### Task Completion
1. Mark task as "Done" in project
2. Update implementation plan with completion checkmarks
3. Create PR with changes
4. Link PR to task issue
5. Request review from assigned reviewer

## Integration with Agents

### Elena's Workflow
1. Analyze requirements for assigned tasks
2. Create detailed specifications
3. Implement business logic
4. Document compliance mappings
5. Delegate to Sage for documentation/stories when needed

### Marcus's Workflow
1. Create project timeline for phases
2. Assess risks for each task
3. Track progress and blockers
4. Generate status reports
5. Delegate to Sage for visualizations/timelines when needed

### Sage's Workflow
1. Receive delegation from Elena or Marcus
2. Generate story/visual via Temporal workflow
3. Create documentation artifacts
4. Return story ID and link
5. Story stored in Zep memory for future reference

## Automation Ideas

### GitHub Actions Workflows

1. **Auto-create issues from plan**
   - Parse markdown on plan updates
   - Create/update issues automatically
   - Set fields based on task metadata

2. **Status sync**
   - Sync PR status to project task status
   - Auto-close tasks when PRs merge
   - Update progress metrics

3. **Weekly reports**
   - Generate status report from project data
   - Post to discussions or create issue
   - Include progress metrics and blockers

## Project Metrics

Track these metrics in the project:

- **Completion Rate**: % of tasks completed per phase
- **Critical Path**: Layer 6 (Guardrails) completion status
- **Owner Velocity**: Tasks completed per owner per week
- **Blockers**: Number of tasks blocked
- **Risk Score**: Based on task priority and dependencies

## Next Steps

1. ✅ Run setup script: `./scripts/setup-github-projects.sh`
2. ✅ Review project structure
3. ⏳ Import tasks from implementation plan
4. ⏳ Assign owners to tasks
5. ⏳ Set up automation workflows
6. ⏳ Begin Phase 1 - Layer 6 Guardrails

---

*Last Updated: December 20, 2024*

