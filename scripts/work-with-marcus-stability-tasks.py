#!/usr/bin/env python3
"""
Work with Marcus to create GitHub project tasks for Enterprise Stability Improvements

This script provides a structured conversation for Marcus to create GitHub issues
for all stability improvement tasks.
"""

print("""
🤖 Working with Marcus to create GitHub project tasks for Enterprise Stability Improvements

Marcus, I need you to create GitHub issues for the Enterprise Stability Improvement plan.

**Context:**
- Stability analysis has been ingested into Zep memory (session: enterprise-stability-analysis-2025-12-30)
- We have a 4-phase improvement plan with 13 tasks
- Each task needs to be created as a GitHub issue

**Instructions:**
1. Read the task list from: scripts/create-stability-github-tasks.md
2. For each task, use create_github_issue with:
   - Title: Task number + name
   - Body: Description + acceptance criteria
   - Labels: As specified in the task list
   - Project: "Enterprise Stability Improvements" (create if needed)

**Priority Order:**
- Phase 1 tasks (Critical/High priority) - Create first
- Phase 2-4 tasks - Create after Phase 1

**Reference:**
- Stability Analysis: docs/stability/enterprise-stability-analysis.md
- Task List: scripts/create-stability-github-tasks.md
- Zep Memory: Search for "enterprise stability analysis" or "stability improvement"

Let's start by creating the Phase 1 tasks (1.1, 1.2, 1.3, 1.4).
""")

print("\n📋 To work with Marcus, use the chat interface and ask:")
print("   'Marcus, please create GitHub issues for the Enterprise Stability Improvement tasks.'")
print("   'Start with Phase 1 tasks (1.1 through 1.4).'")
print("\n   Marcus will use his create_github_issue tool to create the tasks.")

