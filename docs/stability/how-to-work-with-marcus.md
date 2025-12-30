# How to Work with Marcus on Stability Tasks

## Quick Start

The easiest way to interact with Marcus is through the **frontend chat interface**:

1. **Open the Engram frontend** in your browser
2. **Select Marcus** as the active agent
3. **Send this message:**

```
Marcus, I need you to create GitHub issues for the Enterprise Stability Improvement tasks.

**Context:**
- Stability analysis has been ingested into Zep memory (session: enterprise-stability-analysis-2025-12-30)
- We have a 4-phase improvement plan with 13 tasks
- Task structure is documented in: scripts/create-stability-github-tasks.md

**Your Task:**
Please create GitHub issues for all the stability improvement tasks. Start with Phase 1 tasks (1.1, 1.2, 1.3, 1.4) which are Critical/High priority.

**For each task, use create_github_issue with:**
- Title: Task number + name (e.g., "Task 1.1: Health Check Endpoints")
- Body: Description + acceptance criteria from the task list
- Labels: As specified (e.g., "stability", "phase-1", "health-checks", "backend")
- Project: Add to "Enterprise Stability Improvements" project (create if needed)

**Phase 1 Tasks to Create:**
1. Task 1.1: Health Check Endpoints (Critical, Backend)
2. Task 1.2: Configuration Validation on Startup (Critical, Backend)
3. Task 1.3: Graceful Degradation for Zep Memory (High, Memory)
4. Task 1.4: Error Tracking and Logging (High, Error Handling)

**Reference:**
- Search Zep memory for "enterprise stability analysis" or "stability improvement"
- Task details: scripts/create-stability-github-tasks.md
- Full analysis: docs/stability/enterprise-stability-analysis.md

Please start by creating the Phase 1 tasks. After those are created, I'll ask you to create Phase 2-4 tasks.
```

## What Marcus Will Do

1. **Search Zep Memory**: He'll look up the stability analysis we ingested
2. **Read Task List**: He'll reference `scripts/create-stability-github-tasks.md`
3. **Create GitHub Issues**: He'll use his `create_github_issue` tool for each task
4. **Add Labels**: He'll apply the appropriate labels (stability, phase-1, etc.)
5. **Report Back**: He'll tell you which issues were created and their URLs

## Follow-Up Messages

After Phase 1 tasks are created, send:

```
Marcus, please create Phase 2 tasks now (2.1, 2.2, 2.3).
```

Then Phase 3:

```
Marcus, please create Phase 3 tasks now (3.1, 3.2, 3.3).
```

Finally Phase 4:

```
Marcus, please create Phase 4 tasks now (4.1, 4.2, 4.3, 4.4).
```

## Alternative: Command Line (If Auth Token Available)

If you have an authentication token, you can use:

```bash
# Get token (example - adjust for your auth method)
TOKEN=$(az account get-access-token --scope "api://94d50189-d4de-4b80-8804-2f3bf2e2d14f/.default" --query accessToken -o tsv)

# Send message to Marcus
curl -X POST "https://staging-env-api.gentleriver-dd0de193.eastus2.azurecontainerapps.io/api/v1/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Marcus, please create GitHub issues for Phase 1 stability tasks (1.1, 1.2, 1.3, 1.4). Reference the task list in scripts/create-stability-github-tasks.md and the stability analysis in Zep memory.",
    "agent_id": "marcus",
    "session_id": "stability-tasks-cli"
  }'
```

## Verification

After Marcus creates the issues, verify by:

1. **Check GitHub**: Go to the repository and look for new issues
2. **Ask Marcus**: "Marcus, list the GitHub issues you just created"
3. **Check Project**: Verify issues are in the "Enterprise Stability Improvements" project

## Troubleshooting

**If Marcus says he can't find the task list:**
- Remind him: "The task list is in scripts/create-stability-github-tasks.md"
- Or paste the task details directly in your message

**If Marcus says he can't access Zep memory:**
- The stability analysis is in session: `enterprise-stability-analysis-2025-12-30`
- He can search for: "enterprise stability analysis" or "stability improvement"

**If GitHub issue creation fails:**
- Check that GITHUB_TOKEN is configured
- Verify Marcus has access to the repository
- Check GitHub API rate limits

## Files Reference

- **Stability Analysis**: `docs/stability/enterprise-stability-analysis.md`
- **Task List**: `scripts/create-stability-github-tasks.md`
- **Implementation Script**: `scripts/implement-stability-improvements.sh`
- **Zep Memory Session**: `enterprise-stability-analysis-2025-12-30`

