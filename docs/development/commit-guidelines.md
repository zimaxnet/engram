# Commit Guidelines - Preventing Rapid Multiple Commits

## Problem

**Deployments take ~14 minutes.** Multiple commits within this time cause:
- Multiple concurrent GitHub Actions workflows (waste resources)
- Deployment conflicts and failures
- Difficulty tracking which commit caused issues
- Inability to debug deployment problems
- Resource exhaustion from parallel builds

## Solution: Batch Commits

### ✅ Correct Workflow

```bash
# 1. Make ALL related changes across multiple files
# Edit file1.py, file2.py, file3.py, etc.

# 2. Review ALL changes
git status
git diff

# 3. Commit everything at once
git add -A
git commit -m "fix: Complete auth bypass implementation with logging and error handling"
git push
```

### ❌ Incorrect Workflow

```bash
# DON'T do this:
git add file1.py && git commit -m "fix: part 1" && git push
git add file2.py && git commit -m "fix: part 2" && git push  # TOO SOON!
git add file3.py && git commit -m "fix: part 3" && git push  # TOO SOON!
```

## Rules

### 1. Batch All Changes
- Make ALL related changes before committing
- Include all files that are part of the same logical change
- Fix all related issues in one commit

### 2. Review Before Commit
Always run before committing:
```bash
git status          # See what will be committed
git diff            # Review all changes
```

### 3. Single Commit Per Task
- One commit per logical change
- Not one commit per file
- Descriptive commit message covering all changes

### 4. Wait For Deployment To Complete
If you MUST make multiple commits:
- **WAIT FOR DEPLOYMENT TO COMPLETE** (~14 minutes)
- Check deployment status: `gh run list --limit 1`
- Verify conclusion: `gh run list --limit 1 --json conclusion --jq '.[0].conclusion'`
- Only commit if deployment is "success" or "failure" (NOT "in_progress")
- Never commit while deployment is running

### 5. Don't Commit During Deployment
- ⏸️ DO NOT commit while deployment is in progress
- Wait for deployment to complete
- Monitor: `gh run list --limit 1`

## Pre-Commit Hook

A git pre-commit hook prevents rapid commits:
- Warns if committing within 14 minutes of last commit (deployment time)
- Checks if deployment is still in progress via GitHub CLI
- Prompts for confirmation
- Can be bypassed with 'y' if truly necessary (but strongly discouraged)

### Installation

Install the hook for all team members:
```bash
./scripts/install-pre-commit-hook.sh
```

The hook is automatically installed when you clone the repo, but can be reinstalled with the script above.

## Emergency Fixes

Even for urgent fixes:
1. Still batch all related changes
2. Make ONE comprehensive commit
3. Push once
4. Monitor deployment closely

## Examples

### Good Commit
```bash
# Made changes to:
# - backend/api/middleware/auth.py (auth bypass logic)
# - docs/troubleshooting/chat-voice-episodes-401-errors.md (documentation)
# - scripts/diagnose-401-errors.sh (diagnostic script)

git add -A
git commit -m "fix: Implement auth bypass for enterprise POC

- Add AUTH_REQUIRED check at start of get_current_user
- Use security_optional to allow None credentials
- Add comprehensive troubleshooting documentation
- Create diagnostic scripts for 401 errors

Fixes issue where all endpoints returned 401 even with AUTH_REQUIRED=false"
git push
```

### Bad Commits
```bash
# ❌ Three separate commits within seconds:
git add auth.py && git commit -m "fix auth" && git push
git add docs.md && git commit -m "add docs" && git push  # 5 seconds later
git add script.sh && git commit -m "add script" && git push  # 3 seconds later
```

## Monitoring

Check recent commits:
```bash
git log --oneline --since="10 minutes ago"
```

Check deployment status:
```bash
gh run list --limit 5
```

## Related

- See `.cursorrules` for Cursor-specific rules
- See `docs/troubleshooting/chat-voice-episodes-401-errors.md` for deployment impact

