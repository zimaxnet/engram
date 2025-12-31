# Disable Model Router in Azure Container Apps

**Quick Reference** - How to disable Model Router and use direct model

---

## Steps to Disable Model Router

### Option 1: Delete the Environment Variable (Recommended)

1. **Azure Portal** → **Container Apps** → `staging-env-api`
2. **Configuration** → **Environment variables**
3. Find `AZURE_AI_MODEL_ROUTER`
4. Click **Delete** (trash icon)
5. Click **Save**
6. Wait for new revision to deploy (~14 minutes)

### Option 2: Set to Empty String

1. **Azure Portal** → **Container Apps** → `staging-env-api`
2. **Configuration** → **Environment variables**
3. Find `AZURE_AI_MODEL_ROUTER`
4. Click **Edit** (pencil icon)
5. Set **Value** to: `""` (empty string)
6. Click **Save**
7. Wait for new revision to deploy (~14 minutes)

---

## Verify Direct Model is Set

Ensure `AZURE_AI_DEPLOYMENT` is set to your direct model:

1. **Configuration** → **Environment variables**
2. Find `AZURE_AI_DEPLOYMENT`
3. Should be set to: `gpt-5.1-chat` (or `gpt-5-chat` if that's what worked)
4. If not set, add it with value: `gpt-5.1-chat`

---

## After Deployment

Check backend logs for confirmation:

**Should see:**
```
INFO: Using direct model deployment: gpt-5.1-chat (Model Router disabled)
```

**Should NOT see:**
```
INFO: Using Model Router via APIM Gateway: model-router
```

---

## Test

After deployment completes, test chat:

```bash
python3 scripts/test-chat-quick.py --token <JWT_TOKEN> --message "hi"
```

Chat should now work with the direct `gpt-5.1-chat` model.

---

## Re-enable Model Router Later

If you want to re-enable Model Router:

1. Set `AZURE_AI_MODEL_ROUTER` to: `model-router`
2. Save and wait for deployment

