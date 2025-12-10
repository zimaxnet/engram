# Final Resource Inventory - engram-rg

**Date**: 2025-12-09  
**Total Resources**: 11

## Resources Removed ✅

1. **Zep Container App** (`zep`)
   - ✅ Removed - Using Zep Cloud now
   - Cost savings: ~$0-10/month

2. **Storage Account** (`stagingenvstore`)
   - ✅ Removed - Empty and unused
   - Cost savings: ~$1-2/month

3. **Old OpenAI Resource** (`staging-env-openai`)
   - ⚠️ Pending - May require manual deletion via Azure Portal
   - Replaced by `staging-env-openai-v2`

## Remaining Resources (11)

### Container Apps (4)
| Name | Purpose | Scale | Status |
|------|---------|-------|--------|
| `engram-api` | Backend API | 0-10 replicas | ✅ Running |
| `engram-worker` | Temporal Worker | 0-5 replicas | ✅ Running |
| `temporal-server` | Temporal orchestration | 0-3 replicas | ✅ Running |
| `temporal-ui` | Temporal UI | 0-2 replicas | ✅ Running |

### Infrastructure (5)
| Name | Type | Purpose |
|------|------|---------|
| `staging-env-aca` | Container Apps Environment | Hosts all container apps |
| `staging-env-db` | PostgreSQL Flexible Server | Database (B1ms tier) |
| `staging-env-kv-v2-soxm5` | Key Vault | Secrets management |
| `staging-env-logs` | Log Analytics | Observability |
| `staging-env-web` | Static Web App | Frontend hosting |

### Cognitive Services (2)
| Name | Type | Purpose |
|------|------|---------|
| `staging-env-openai-v2` | OpenAI | LLM services |
| `staging-env-speech-v2` | Speech Services | STT/TTS |

## Cost Optimization Status

### ✅ Optimized
- All container apps use **scale-to-zero** (minReplicas: 0)
- PostgreSQL uses **B1ms** (burstable, cost-effective tier)
- Log Analytics has **30-day retention** (reasonable for PoC)
- Static Web App uses **Standard tier** (required for custom domains)

### 💰 Estimated Monthly Costs

| Category | Resource | Est. Cost |
|----------|----------|-----------|
| **Compute** | Container Apps (scale-to-zero) | $0-25 |
| **Database** | PostgreSQL B1ms | ~$13 |
| **Storage** | Log Analytics (30-day) | ~$5-10 |
| **Frontend** | Static Web App Standard | ~$9 |
| **AI Services** | OpenAI + Speech (usage-based) | Variable |
| **Infrastructure** | Key Vault, Environment | ~$1-2 |
| **Total (Idle)** | | **~$28-60/month** |
| **Total (Active)** | | **~$50-200/month** |

## Recommendations

1. ✅ **Zep Cloud migration** - Complete (container removed)
2. ⚠️ **Old OpenAI cleanup** - May need manual deletion via portal
3. ✅ **Storage account** - Removed (was unused)
4. ✅ **All resources optimized** - Scale-to-zero enabled where possible

## Verification Commands

```bash
# List all resources
az resource list --resource-group engram-rg --query "[].{Name:name, Type:type}" -o table

# Check container apps
az containerapp list --resource-group engram-rg --query "[].{Name:name, Status:properties.runningStatus, MinReplicas:properties.template.scale.minReplicas}" -o table

# Check costs (requires Cost Management API)
az consumption usage list --start-date $(date -u -d '1 month ago' +%Y-%m-%d) --end-date $(date -u +%Y-%m-%d) --query "[?contains(instanceName, 'engram-rg')]" -o table
```

