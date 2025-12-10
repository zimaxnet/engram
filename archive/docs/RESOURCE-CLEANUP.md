# Resource Cleanup Plan

## Current Resources in engram-rg

### Container Apps
- ✅ `engram-api` - **KEEP** (Backend API)
- ✅ `engram-worker` - **KEEP** (Temporal Worker)
- ✅ `temporal-server` - **KEEP** (Temporal orchestration)
- ✅ `temporal-ui` - **KEEP** (Temporal UI)
- ❌ `zep` - **REMOVE** (Using Zep Cloud now, not self-hosted)

### Cognitive Services
- ❌ `staging-env-openai` - **REMOVE** (Old, replaced by v2)
- ✅ `staging-env-openai-v2` - **KEEP** (Active OpenAI resource)
- ✅ `staging-env-speech-v2` - **KEEP** (Speech Services)

### Storage
- ⚠️ `stagingenvstore` - **REVIEW** (May be unused, check if ETL pipeline uses it)

### Infrastructure
- ✅ `staging-env-aca` - **KEEP** (Container Apps Environment)
- ✅ `staging-env-db` - **KEEP** (PostgreSQL)
- ✅ `staging-env-kv-v2-soxm5` - **KEEP** (Key Vault)
- ✅ `staging-env-logs` - **KEEP** (Log Analytics)
- ✅ `staging-env-web` - **KEEP** (Static Web App)

## Resources to Remove

### 1. Zep Container App
**Reason**: We're using Zep Cloud (`app.getzep.com`) instead of self-hosted container.

**Impact**: 
- Backend still points to it, but will be updated on next deployment
- No data loss (using Zep Cloud)
- Saves: ~$0-10/month (scale-to-zero, but still has base cost)

**Command**:
```bash
az containerapp delete \
  --name zep \
  --resource-group engram-rg \
  --yes
```

### 2. Old OpenAI Resource (`staging-env-openai`)
**Reason**: Replaced by `staging-env-openai-v2`.

**Impact**:
- Verify v2 is actually being used
- Saves: ~$0/month if unused, but cleanup is good practice

**Command**:
```bash
az cognitiveservices account delete \
  --name staging-env-openai \
  --resource-group engram-rg \
  --yes
```

### 3. Storage Account (`stagingenvstore`)
**Reason**: May be unused if ETL pipeline isn't active.

**Impact**:
- Check if ETL pipeline uses it
- If unused, saves: ~$1-2/month
- **CAUTION**: Verify no data needed before deletion

**Command** (if confirmed unused):
```bash
az storage account delete \
  --name stagingenvstore \
  --resource-group engram-rg \
  --yes
```

## Cost Savings Estimate

| Resource | Monthly Cost | Status |
|----------|--------------|--------|
| Zep Container App | $0-10 | Remove |
| Old OpenAI | $0 (if unused) | Remove |
| Storage Account | $1-2 (if unused) | Review |
| **Total Potential Savings** | **$1-12/month** | |

## Verification Before Removal

1. **Zep Container**: Verify backend will use Zep Cloud on next deployment
2. **Old OpenAI**: Verify v2 is the active endpoint
3. **Storage Account**: Check ETL pipeline usage

## Safe Removal Order

1. Remove Zep container (after confirming backend will use Zep Cloud)
2. Remove old OpenAI (after verifying v2 is active)
3. Review and remove storage account (if confirmed unused)

