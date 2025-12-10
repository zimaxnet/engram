# Engram Deployment Inventory & Comparison

**Date**: December 9, 2025  
**Environment**: `staging-env`  
**Resource Group**: `engram-rg`  
**Location**: `eastus2`

---

## Executive Summary

✅ **Overall Status**: **14/14 Core Resources Deployed** (100%)

All planned infrastructure components are successfully deployed and running. There are minor discrepancies (duplicate OpenAI account from previous deployment) but all required resources are operational.

---

## Resource Inventory

### ✅ Core Infrastructure (5/5)

| Resource Type | Planned | Deployed | Status | Notes |
|--------------|---------|----------|--------|-------|
| **Log Analytics Workspace** | `staging-env-logs` | `staging-env-logs` | ✅ | 30-day retention configured |
| **Container Apps Environment** | `staging-env-aca` | `staging-env-aca` | ✅ | Managed environment for all container apps |
| **PostgreSQL Flexible Server** | `staging-env-db` | `staging-env-db` | ✅ | PostgreSQL 13, B1ms SKU, Ready state |
| **Storage Account** | `stagingenvstore` | `stagingenvstore` | ✅ | Standard_LRS, StorageV2 |
| **Key Vault** | `staging-env-kv-v2-*` | `staging-env-kv-v2-soxm5` | ✅ | RBAC enabled, secrets configured |

### ✅ Container Apps (5/5)

| Container App | Planned | Deployed | Status | FQDN | Min/Max Replicas |
|--------------|---------|----------|--------|------|------------------|
| **Backend API** | `engram-api` | `engram-api` | ✅ Running | `engram-api.calmgrass-018b2019.eastus2.azurecontainerapps.io` | 0/10 |
| **Worker** | `engram-worker` | `engram-worker` | ✅ Running | `engram-worker.internal.calmgrass-018b2019.eastus2.azurecontainerapps.io` | 0/5 |
| **Temporal Server** | `temporal-server` | `temporal-server` | ✅ Running | `temporal-server.internal.calmgrass-018b2019.eastus2.azurecontainerapps.io` | 0/3 |
| **Temporal UI** | `temporal-ui` | `temporal-ui` | ✅ Running | `temporal-ui.calmgrass-018b2019.eastus2.azurecontainerapps.io` | 0/2 |
| **Zep** | `zep` | `zep` | ✅ Running | `zep.calmgrass-018b2019.eastus2.azurecontainerapps.io` | 0/3 |

**Note**: All container apps are configured with scale-to-zero (minReplicas: 0) for cost optimization, which is correct per plan.

### ✅ Cognitive Services (3/3)

| Service | Planned | Deployed | Status | Endpoint |
|---------|---------|----------|--------|----------|
| **Azure OpenAI** | `staging-env-openai-v2` | `staging-env-openai-v2` | ✅ | `https://staging-env-openai-v2.openai.azure.com/` |
| **Azure Speech** | `staging-env-speech-v2` | `staging-env-speech-v2` | ✅ | `https://staging-env-speech-v2.cognitiveservices.azure.com/` |
| **Legacy OpenAI** | N/A | `staging-env-openai` | ⚠️ Legacy | `https://staging-env-openai.openai.azure.com/` |

**Note**: `staging-env-openai` is a legacy resource from a previous deployment. It's not used by the current infrastructure but can be cleaned up.

### ✅ Frontend (1/1)

| Resource | Planned | Deployed | Status | Hostname |
|----------|---------|----------|--------|----------|
| **Static Web App** | `staging-env-web` | `staging-env-web` | ✅ | `calm-smoke-06afc910f.3.azurestaticapps.net` |

---

## Detailed Comparison

### ✅ Infrastructure Components

#### 1. Log Analytics Workspace
- **Planned**: `staging-env-logs` with 30-day retention
- **Deployed**: ✅ `staging-env-logs` in `eastus2`
- **Status**: ✅ Matches plan

#### 2. Container Apps Environment
- **Planned**: `staging-env-aca` with Log Analytics integration
- **Deployed**: ✅ `staging-env-aca` in `eastus2`
- **Status**: ✅ Matches plan

#### 3. PostgreSQL Flexible Server
- **Planned**: `staging-env-db`, PostgreSQL 13, B1ms SKU, 32GB storage
- **Deployed**: ✅ `staging-env-db`, PostgreSQL 13, Ready state
- **FQDN**: `staging-env-db.postgres.database.azure.com`
- **Status**: ✅ Matches plan

#### 4. Storage Account
- **Planned**: `stagingenvstore`, Standard_LRS, StorageV2
- **Deployed**: ✅ `stagingenvstore`, Standard_LRS, StorageV2
- **Status**: ✅ Matches plan

#### 5. Key Vault
- **Planned**: `staging-env-kv-v2-{unique}` with RBAC
- **Deployed**: ✅ `staging-env-kv-v2-soxm5` with RBAC
- **URI**: `https://staging-env-kv-v2-soxm5.vault.azure.net/`
- **Status**: ✅ Matches plan

### ✅ Container Apps

#### 1. Backend API (`engram-api`)
- **Planned**: Backend API with ingress enabled
- **Deployed**: ✅ Running, public ingress enabled
- **FQDN**: `engram-api.calmgrass-018b2019.eastus2.azurecontainerapps.io`
- **Scaling**: 0-10 replicas (scale-to-zero enabled)
- **Status**: ✅ Matches plan

#### 2. Worker (`engram-worker`)
- **Planned**: Temporal worker with internal ingress
- **Deployed**: ✅ Running, internal ingress
- **FQDN**: `engram-worker.internal.calmgrass-018b2019.eastus2.azurecontainerapps.io`
- **Scaling**: 0-5 replicas (scale-to-zero enabled)
- **Status**: ✅ Matches plan

#### 3. Temporal Server (`temporal-server`)
- **Planned**: Temporal server with internal ingress
- **Deployed**: ✅ Running, internal ingress
- **FQDN**: `temporal-server.internal.calmgrass-018b2019.eastus2.azurecontainerapps.io`
- **Scaling**: 0-3 replicas (scale-to-zero enabled)
- **Status**: ✅ Matches plan

#### 4. Temporal UI (`temporal-ui`)
- **Planned**: Temporal UI with public ingress
- **Deployed**: ✅ Running, public ingress enabled
- **FQDN**: `temporal-ui.calmgrass-018b2019.eastus2.azurecontainerapps.io`
- **Scaling**: 0-2 replicas (scale-to-zero enabled)
- **Status**: ✅ Matches plan

#### 5. Zep (`zep`)
- **Planned**: Zep service (optional, using hosted)
- **Deployed**: ✅ Running, public ingress enabled
- **FQDN**: `zep.calmgrass-018b2019.eastus2.azurecontainerapps.io`
- **Scaling**: 0-3 replicas (scale-to-zero enabled)
- **Status**: ✅ Matches plan (deployed but using hosted Zep Cloud in practice)

### ✅ Cognitive Services

#### 1. Azure OpenAI
- **Planned**: `staging-env-openai-v2`
- **Deployed**: ✅ `staging-env-openai-v2`
- **Endpoint**: `https://staging-env-openai-v2.openai.azure.com/`
- **Status**: ✅ Matches plan

#### 2. Azure Speech Services
- **Planned**: `staging-env-speech-v2`
- **Deployed**: ✅ `staging-env-speech-v2`
- **Endpoint**: `https://staging-env-speech-v2.cognitiveservices.azure.com/`
- **Status**: ✅ Matches plan

#### 3. Legacy OpenAI (Cleanup Candidate)
- **Planned**: N/A
- **Deployed**: ⚠️ `staging-env-openai` (legacy)
- **Endpoint**: `https://staging-env-openai.openai.azure.com/`
- **Status**: ⚠️ Legacy resource, not used by current infrastructure
- **Action**: Can be deleted to reduce costs

### ✅ Frontend

#### Static Web App
- **Planned**: `staging-env-web`
- **Deployed**: ✅ `staging-env-web`
- **Hostname**: `calm-smoke-06afc910f.3.azurestaticapps.net`
- **Status**: ✅ Matches plan

---

## Configuration Verification

### ✅ Scale-to-Zero Configuration
All container apps are correctly configured with `minReplicas: 0`:
- ✅ Backend API: 0-10 replicas
- ✅ Worker: 0-5 replicas
- ✅ Temporal Server: 0-3 replicas
- ✅ Temporal UI: 0-2 replicas
- ✅ Zep: 0-3 replicas

**Status**: ✅ Matches plan (FinOps-first architecture)

### ✅ Ingress Configuration
- ✅ Backend API: Public ingress enabled
- ✅ Worker: Internal ingress (correct)
- ✅ Temporal Server: Internal ingress (correct)
- ✅ Temporal UI: Public ingress enabled
- ✅ Zep: Public ingress enabled

**Status**: ✅ Matches plan

### ✅ Networking
- ✅ All resources in `eastus2` region
- ✅ Container Apps in same managed environment
- ✅ Internal communication via internal ingress
- ✅ Public endpoints properly configured

**Status**: ✅ Matches plan

---

## Discrepancies & Notes

### ⚠️ Minor Issues

1. **Legacy OpenAI Account**
   - **Issue**: `staging-env-openai` exists but is not used
   - **Impact**: Low (unused resource, minimal cost)
   - **Action**: Can be deleted in cleanup
   - **Priority**: Low

### ✅ All Critical Resources Deployed

All resources required for the PoC are deployed and operational:
- ✅ Core infrastructure (Log Analytics, ACA Environment, PostgreSQL, Storage, Key Vault)
- ✅ All container apps (Backend, Worker, Temporal Server/UI, Zep)
- ✅ Cognitive Services (OpenAI v2, Speech v2)
- ✅ Frontend (Static Web App)

---

## Endpoint Summary

### Public Endpoints
- **Backend API**: `https://engram-api.calmgrass-018b2019.eastus2.azurecontainerapps.io`
- **Temporal UI**: `https://temporal-ui.calmgrass-018b2019.eastus2.azurecontainerapps.io`
- **Zep API**: `https://zep.calmgrass-018b2019.eastus2.azurecontainerapps.io`
- **Frontend**: `https://calm-smoke-06afc910f.3.azurestaticapps.net`

### Internal Endpoints
- **Worker**: `engram-worker.internal.calmgrass-018b2019.eastus2.azurecontainerapps.io`
- **Temporal Server**: `temporal-server.internal.calmgrass-018b2019.eastus2.azurecontainerapps.io`

### Database
- **PostgreSQL**: `staging-env-db.postgres.database.azure.com`

### Key Vault
- **Key Vault**: `https://staging-env-kv-v2-soxm5.vault.azure.net/`

---

## Cost Optimization Verification

### ✅ Scale-to-Zero Enabled
All container apps configured with `minReplicas: 0`, enabling scale-to-zero when idle.

### ✅ Appropriate SKU Sizes
- PostgreSQL: B1ms (Burstable, cost-effective for PoC)
- Storage: Standard_LRS (lowest cost option)
- Log Analytics: PerGB2018 (pay-per-use)

### ⚠️ Cleanup Opportunity
- Legacy OpenAI account (`staging-env-openai`) can be deleted

---

## Deployment Health

### ✅ All Services Running
- All 5 container apps in "Running" status
- PostgreSQL in "Ready" state
- All Cognitive Services active
- Static Web App deployed

### ✅ Connectivity
- Backend API accessible (may need cold start on first request)
- Frontend deployed and accessible
- Internal services properly configured

---

## Recommendations

### Immediate Actions
1. ✅ **None Required** - All critical resources deployed

### Optional Cleanup
1. ⚠️ **Delete Legacy OpenAI**: Remove `staging-env-openai` to reduce costs

### Future Enhancements
1. Monitor cold start times for scale-to-zero services
2. Consider Application Insights dashboards for observability
3. Set up alerting for service health

---

## Conclusion

✅ **Deployment Status**: **100% Complete**

All planned infrastructure components are successfully deployed and operational. The deployment matches the Bicep templates and PoC plan. The only discrepancy is a legacy OpenAI account that can be cleaned up.

**Ready for**: PoC demonstration and testing

---

**Last Updated**: December 9, 2025  
**Inventory Date**: December 9, 2025

