# GitHub Integration Authorization Guide

## Overview

Elena and Marcus agents are authorized to interact with GitHub Projects and Issues to track the Production-Grade System Implementation plan. This document explains the authorization model and how agents interact with GitHub.

## Authorization Model

### GitHub Token Configuration

Agents use a **GitHub Personal Access Token (PAT)** or **GitHub App token** to authenticate with the GitHub API.

**Environment Variable:**
```bash
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

**Configuration:**
- Token is stored in `backend/core/config.py` as `github_token`
- Can be set via environment variable `GITHUB_TOKEN`
- For production, store in Azure Key Vault as secret `github-token`

### Token Permissions Required

The GitHub token needs the following scopes:

| Scope | Purpose | Required For |
|-------|---------|--------------|
| `repo` | Full repository access | Creating/updating issues |
| `read:project` | Read project data | Querying project status |
| `write:project` | Write project data | Adding issues to projects (future) |

**Note:** For GitHub Projects API v2 (GraphQL), additional permissions may be needed.

### Repository Configuration

```bash
GITHUB_REPO_OWNER=zimaxnet
GITHUB_REPO_NAME=engram
```

## Agent Capabilities

### Elena (Business Analyst)

**Authorized Actions:**
- ✅ Create GitHub issues for requirements tasks
- ✅ Update issue status and progress
- ✅ Query project status
- ✅ List assigned tasks
- ✅ Close completed tasks

**Use Cases:**
- Creating issues for requirements analysis tasks
- Tracking compliance mapping progress
- Updating task status as work progresses
- Checking overall project health

### Marcus (Project Manager)

**Authorized Actions:**
- ✅ Create GitHub issues for project management tasks
- ✅ Update issue status and progress
- ✅ Query project status and metrics
- ✅ List assigned tasks
- ✅ Close completed tasks
- ✅ Generate status reports from GitHub data

**Use Cases:**
- Creating issues for execution guardrails tasks
- Tracking timeline and milestones
- Generating status reports from GitHub data
- Monitoring critical path tasks

## System Awareness

### How Engram Tracks Progress

1. **GitHub Issues as Tasks**
   - Each task in the implementation plan can be represented as a GitHub issue
   - Issues are labeled with: `production-grade-system`, layer name, phase name
   - Issues are assigned to agents (Elena/Marcus) via labels

2. **Progress Tracking**
   - Agents can query `get_project_status` to see:
     - Total tasks
     - Completed tasks
     - Open tasks
     - Critical tasks
     - Progress percentage

3. **Automatic Updates**
   - Agents can update issues as they work
   - Status changes (open → closed) reflect progress
   - Body updates can include progress notes

### Integration Points

**Agent Workflow:**
```
1. Agent receives task assignment
2. Agent creates GitHub issue (if not exists)
3. Agent works on task
4. Agent updates issue with progress
5. Agent closes issue when complete
6. System tracks progress via GitHub API
```

**System Monitoring:**
- Backend can query GitHub API to get project status
- Frontend can display progress metrics
- Agents are aware of their assigned tasks

## Security Considerations

### Token Storage

**Development:**
- Token in `.env` file (not committed to git)
- `.env` in `.gitignore`

**Production:**
- Token stored in Azure Key Vault
- Retrieved via `DefaultAzureCredential`
- Never exposed in logs or responses

### Access Control

**Current Model:**
- Single token for all agent actions
- Token has repository-level permissions
- All agents share the same token

**Future Enhancement:**
- GitHub App with per-agent tokens
- Fine-grained permissions per agent
- Audit logging of agent actions

### Rate Limiting

GitHub API has rate limits:
- **Authenticated requests**: 5,000/hour
- **Unauthenticated requests**: 60/hour

Agents should:
- Batch operations when possible
- Cache project status queries
- Respect rate limit headers

## Usage Examples

### Elena Creating a Task

```python
# Elena can create an issue for a requirements task
result = await create_github_issue_tool(
    title="Task 6.1: Input Guardrails Implementation",
    body="Implement prompt injection detection and PII redaction...",
    labels="production-grade-system,Layer 6: Guardrails,Phase 1: Critical Security",
    assignee="elena"
)
```

### Marcus Checking Progress

```python
# Marcus can check overall project status
status = await get_project_status_tool()
# Returns: Progress percentage, task counts, status
```

### Agent Updating Progress

```python
# Agent updates issue as they work
result = await update_github_issue_tool(
    issue_number=123,
    body="Progress update: Completed PII redaction module...",
    labels="production-grade-system,Layer 6: Guardrails,in-progress"
)
```

## Setup Instructions

### 1. Create GitHub Personal Access Token

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token
3. Select scopes: `repo`, `read:project`, `write:project`
4. Copy token

### 2. Configure Environment

**Local Development:**
```bash
# .env file
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
GITHUB_REPO_OWNER=zimaxnet
GITHUB_REPO_NAME=engram
```

**Azure Container Apps:**
```bash
# Set as environment variable or secret
az containerapp update \
  --name backend-aca \
  --resource-group engram-rg \
  --set-env-vars GITHUB_TOKEN=ghp_xxx \
                 GITHUB_REPO_OWNER=zimaxnet \
                 GITHUB_REPO_NAME=engram
```

**Azure Key Vault (Recommended for Production):**
```bash
az keyvault secret set \
  --vault-name engram-kv \
  --name github-token \
  --value ghp_xxx
```

### 3. Test Integration

```python
# Test from Python
from backend.integrations.github_client import get_github_client

client = get_github_client()
status = await client.get_project_status()
print(status)
```

## Limitations

### Current Limitations

1. **Project API v2 (GraphQL)**
   - Adding issues to projects requires GraphQL API
   - Not yet implemented (placeholder in code)
   - Issues must be manually added to projects via UI

2. **Issue Assignment**
   - Can't directly assign to GitHub usernames
   - Using labels for agent identification
   - Future: Map agents to GitHub usernames

3. **Project Fields**
   - Can't update custom project fields (Status, Priority, etc.)
   - Requires GraphQL API implementation
   - Future: Full project field support

### Workarounds

1. **Manual Project Addition**
   - Create issues via API
   - Manually add to project via GitHub UI
   - Or use GitHub CLI: `gh project item-add <project-id> --owner <issue-id>`

2. **Label-Based Tracking**
   - Use labels: `owner:elena`, `owner:marcus`
   - Filter issues by labels
   - Track progress via label counts

## Future Enhancements

1. **GraphQL API Integration**
   - Full GitHub Projects API v2 support
   - Update project fields programmatically
   - Add issues to projects automatically

2. **GitHub App**
   - Per-agent authentication
   - Fine-grained permissions
   - Better audit trail

3. **Automated Sync**
   - Sync implementation plan → GitHub issues
   - Auto-create issues for new tasks
   - Auto-update fields from plan

4. **Progress Dashboard**
   - Real-time progress visualization
   - Agent workload distribution
   - Critical path tracking

## Troubleshooting

### "GitHub token not configured"

**Solution:**
- Set `GITHUB_TOKEN` environment variable
- Or configure in Azure Key Vault
- Restart backend service

### "Failed to create issue: 401 Unauthorized"

**Solution:**
- Check token is valid
- Verify token has `repo` scope
- Token may have expired

### "Failed to get project status"

**Solution:**
- Check token has `read:project` scope
- Verify repository name/owner is correct
- Check network connectivity

## References

- [GitHub REST API](https://docs.github.com/en/rest)
- [GitHub Projects API v2 (GraphQL)](https://docs.github.com/en/graphql/reference/objects#projectv2)
- [GitHub Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)

---

*Last Updated: December 20, 2024*

