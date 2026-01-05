---
layout: default
title: "Marcus Validation Prompt"
parent: "Operations"
---

# Marcus Validation Prompt

Copy and paste this prompt into the Engram frontend chat interface with Marcus selected:

---

Marcus, I need you to validate that you can perform all the tasks for creating GitHub issues for the Enterprise Stability Improvement plan. Please confirm the following:

**1. Memory Access:**
- Can you search Zep memory for the stability analysis? 
- Search for: "enterprise stability analysis" or session "enterprise-stability-analysis-2025-12-30"
- Confirm you can access the root cause analysis and 4-phase improvement plan

**2. Task List Access:**
- Can you read the task list from: scripts/create-stability-github-tasks.md?
- Confirm you can see all 13 tasks across 4 phases:
  - Phase 1: Tasks 1.1, 1.2, 1.3, 1.4 (Critical/High priority)
  - Phase 2: Tasks 2.1, 2.2, 2.3 (Configuration robustness)
  - Phase 3: Tasks 3.1, 3.2, 3.3 (Service resilience)
  - Phase 4: Tasks 4.1, 4.2, 4.3, 4.4 (Deployment reliability)

**3. GitHub Integration:**
- Do you have access to the create_github_issue tool?
- Can you create issues with:
  - Title (Task number + name)
  - Body (Description + acceptance criteria)
  - Labels (stability, phase-X, etc.)
  - Project assignment ("Enterprise Stability Improvements")

**4. Task Understanding:**
For each task, you need to:
- Extract the task number, name, and description
- Include all acceptance criteria in the issue body
- Apply the correct labels (stability, phase-1/2/3/4, and category labels)
- Set appropriate priority based on the task

**5. Execution Plan:**
- Confirm you'll start with Phase 1 tasks (1.1, 1.2, 1.3, 1.4)
- After Phase 1, proceed to Phase 2, then 3, then 4
- Report back with issue numbers and URLs for each created issue

**Please respond with:**
1. ✅ or ❌ for each capability above
2. A summary of what you found in Zep memory about the stability analysis
3. Confirmation that you're ready to create the GitHub issues
4. Any blockers or issues you've identified

Once you confirm all capabilities, I'll ask you to proceed with creating the Phase 1 tasks.

---

