# VoiceLive & Chat SOP: Multi-Environment Deployment

## Standard Operating Procedures for Voice and Chat Services

**Document Version:** 1.0  
**Last Updated:** December 2025  
**Classification:** Internal Operations  
**Compliance:** NIST AI RMF, SOC2 Type II

---

## 1. Environment Overview

| Level | Environment | Purpose | Auth Model | Data Classification |
|-------|-------------|---------|------------|---------------------|
| 1 | **Staging POC** | Proof of concept, demos | Dev tokens + API Key | Non-sensitive |
| 2 | **Development** | Feature development | Dev tokens | Synthetic only |
| 3 | **Test** | Integration testing | Service Principal | Synthetic only |
| 4 | **UAT** | User acceptance | Entra ID (test tenant) | Anonymized |
| 5 | **Production** | Live operations | Entra ID + MFA | Production data |

---

## 2. Level 1: Staging POC

### 2.1 Purpose
- Demonstrate capabilities to stakeholders
- Validate Azure AI integration
- Test VoiceLive real-time features
- Quick iteration without security overhead

### 2.2 Configuration

```bash
# Environment Variables
ENVIRONMENT=development
DEBUG=true

# VoiceLive Configuration
AZURE_VOICELIVE_ENDPOINT=https://zimax.services.ai.azure.com
AZURE_VOICELIVE_MODEL=gpt-realtime
AZURE_VOICELIVE_VOICE=en-US-Ava:DragonHDLatestNeural

# Chat Configuration (APIM Gateway)
AZURE_AI_ENDPOINT=https://zimax-gw.azure-api.net/zimax/openai/v1
AZURE_AI_DEPLOYMENT=gpt-5.1-chat
```

### 2.3 Authentication
```bash
# Dev token format (no validation)
Authorization: Bearer dev_<user_id>

# Example
curl -X POST https://staging-env-api.../api/v1/chat \
  -H "Authorization: Bearer dev_testuser" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "session_id": "demo-1"}'
```

### 2.4 Azure Resources
| Resource | Name | Configuration |
|----------|------|---------------|
| Container App | staging-env-api | 0.5 vCPU, 1GB RAM, scale 0-3 |
| Key Vault | stagingenvkv* | RBAC enabled |
| AI Services | zimax | VoiceLive + Chat |

### 2.5 Operational Procedures

#### Deploy
```bash
# Trigger via GitHub Actions
gh workflow run deploy.yml -f environment=staging

# Or manual Azure CLI
az containerapp update --name staging-env-api --resource-group engram-rg \
  --set-env-vars "AZURE_VOICELIVE_ENDPOINT=https://zimax.services.ai.azure.com"
```

#### Test Voice
```bash
# Check status
curl https://staging-env-api.gentleriver-dd0de193.eastus2.azurecontainerapps.io/api/v1/voice/status

# WebSocket connection (from frontend)
wss://staging-env-api.gentleriver-dd0de193.eastus2.azurecontainerapps.io/api/v1/voice/ws
```

#### Test Chat
```bash
curl -X POST https://staging-env-api.../api/v1/chat \
  -H "Authorization: Bearer dev_demo" \
  -H "Content-Type: application/json" \
  -d '{"message": "Analyze requirements for CRM migration", "session_id": "poc-demo"}'
```

### 2.6 Monitoring
- Azure Container Apps logs (basic)
- No alerting required
- Manual health checks

---

## 3. Level 2: Development

### 3.1 Purpose
- Active feature development
- Developer testing
- Integration with local IDEs
- Debugging and tracing

### 3.2 Configuration

```bash
# Environment Variables
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# VoiceLive - Same as staging
AZURE_VOICELIVE_ENDPOINT=https://zimax.services.ai.azure.com
AZURE_VOICELIVE_MODEL=gpt-realtime

# Chat - Development deployment
AZURE_AI_ENDPOINT=https://zimax-gw.azure-api.net/zimax/openai/v1
AZURE_AI_DEPLOYMENT=gpt-5.1-chat

# Tracing enabled
APPLICATIONINSIGHTS_CONNECTION_STRING=<dev-app-insights>
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

### 3.3 Authentication
```bash
# Dev tokens with role simulation
Authorization: Bearer dev_<user_id>_<role>

# Examples
dev_alice_analyst     # Business Analyst role
dev_bob_admin         # Admin role
dev_carol_viewer      # Read-only role
```

### 3.4 Local Development Setup
```bash
# Clone and setup
git clone https://github.com/zimaxnet/engram.git
cd engram
python -m venv venv && source venv/bin/activate
pip install -r backend/requirements.txt

# Create .env from template
cp .env.example .env
# Edit with dev credentials

# Run locally
uvicorn backend.api.main:app --reload --port 8082

# Test voice locally
curl http://localhost:8082/api/v1/voice/status
```

### 3.5 Operational Procedures

#### Feature Branch Workflow
```bash
# Create feature branch
git checkout -b feature/voice-enhancement

# Make changes, test locally
pytest backend/tests -v

# Push and create PR
git push -u origin feature/voice-enhancement
gh pr create --title "Voice: Add interruption handling"
```

#### Debug VoiceLive
```python
# Enable detailed logging in code
import logging
logging.getLogger("backend.voice").setLevel(logging.DEBUG)

# Check WebSocket frames
# Use browser DevTools Network tab > WS filter
```

### 3.6 Monitoring
- Local logging to stdout
- Application Insights (dev workspace)
- Jaeger for distributed tracing (optional)

---

## 4. Level 3: Test

### 4.1 Purpose
- Automated testing
- CI/CD integration
- Performance baseline
- Security scanning

### 4.2 Configuration

```bash
# Environment Variables
ENVIRONMENT=test
DEBUG=false
LOG_LEVEL=INFO

# VoiceLive - Dedicated test resource
AZURE_VOICELIVE_ENDPOINT=https://zimax-test.services.ai.azure.com
AZURE_VOICELIVE_MODEL=gpt-realtime

# Chat - Test deployment with rate limiting
AZURE_AI_ENDPOINT=https://zimax-gw.azure-api.net/zimax-test/openai/v1
AZURE_AI_DEPLOYMENT=gpt-5.1-chat

# Test database
DATABASE_URL=postgresql://test_user@test-postgres/engram_test
```

### 4.3 Authentication
```bash
# Service Principal (non-interactive)
AZURE_CLIENT_ID=<test-sp-client-id>
AZURE_CLIENT_SECRET=<test-sp-secret>
AZURE_TENANT_ID=<tenant-id>

# DefaultAzureCredential picks up automatically
```

### 4.4 Azure Resources
| Resource | Name | Configuration |
|----------|------|---------------|
| Container App | test-env-api | 0.5 vCPU, 1GB RAM, scale 0-2 |
| AI Services | zimax-test | Separate quota |
| PostgreSQL | test-postgres | Basic tier, auto-purge |

### 4.5 Operational Procedures

#### Run E2E Tests
```bash
# Via GitHub Actions
gh workflow run e2e-tests.yml -f environment=test -f test_suite=all

# Manual test run
npx playwright test --grep @voice
npx playwright test --grep @chat
```

#### Performance Testing
```bash
# Load test chat endpoint
k6 run scripts/load-tests/chat-load.js

# Voice WebSocket stress test
k6 run scripts/load-tests/voice-ws-stress.js
```

#### Security Scan
```bash
# Dependency scan
pip-audit -r backend/requirements.txt

# Container scan
trivy image ghcr.io/zimaxnet/engram/backend:latest
```

### 4.6 Monitoring
- Application Insights (test workspace)
- Test result artifacts in GitHub Actions
- Weekly security reports

---

## 5. Level 4: UAT (User Acceptance Testing)

### 5.1 Purpose
- Business user validation
- Workflow verification
- Accessibility testing
- Final sign-off before production

### 5.2 Configuration

```bash
# Environment Variables
ENVIRONMENT=uat
DEBUG=false
LOG_LEVEL=INFO

# VoiceLive - Production-like
AZURE_VOICELIVE_ENDPOINT=https://zimax.services.ai.azure.com
AZURE_VOICELIVE_MODEL=gpt-realtime
AZURE_VOICELIVE_VOICE=en-US-Ava:DragonHDLatestNeural

# Chat - Production gateway, UAT deployment
AZURE_AI_ENDPOINT=https://zimax-gw.azure-api.net/zimax/openai/v1
AZURE_AI_DEPLOYMENT=gpt-5.1-chat

# UAT database with anonymized data
DATABASE_URL=postgresql://uat_user@uat-postgres/engram_uat
```

### 5.3 Authentication
```bash
# Entra ID with test tenant
# Users authenticate via browser SSO
# Test accounts provisioned in Entra ID test tenant

# Required claims
- oid (Object ID)
- preferred_username
- roles (engram.user, engram.analyst, engram.admin)
```

### 5.4 User Provisioning
```bash
# Create UAT test users in Entra ID
az ad user create \
  --display-name "UAT Tester 1" \
  --user-principal-name uat.tester1@zimaxtest.onmicrosoft.com \
  --password "TempP@ss123!"

# Assign roles
az ad app role assignment add \
  --id <app-id> \
  --principal-id <user-oid> \
  --role-id <engram.analyst-role-id>
```

### 5.5 Operational Procedures

#### UAT Deployment
```bash
# Deploy to UAT
gh workflow run deploy.yml -f environment=uat

# Verify health
curl https://uat-env-api.../health
curl https://uat-env-api.../api/v1/voice/status
```

#### UAT Test Scenarios
```markdown
## Voice Test Cases
1. [ ] Start voice session with Elena
2. [ ] Speak requirements, verify transcription
3. [ ] Switch to Marcus mid-conversation
4. [ ] Verify voice characteristics match agent
5. [ ] Test interruption handling
6. [ ] Test poor network simulation

## Chat Test Cases
1. [ ] Send text message, verify response
2. [ ] Test multi-turn conversation
3. [ ] Verify memory persistence
4. [ ] Test agent switching
5. [ ] Verify facts extraction
```

#### Sign-off Process
```markdown
## UAT Sign-off Checklist
- [ ] All test cases passed
- [ ] Accessibility review complete
- [ ] Performance acceptable
- [ ] Security review approved
- [ ] Business stakeholder sign-off
- [ ] Ready for production deployment
```

### 5.6 Monitoring
- Application Insights (UAT workspace)
- User feedback collection
- Session recordings (with consent)

---

## 6. Level 5: Production

### 6.1 Purpose
- Live customer operations
- Full security enforcement
- High availability
- Compliance audit trail

### 6.2 Configuration

```bash
# Environment Variables
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING

# VoiceLive - Production with HA
AZURE_VOICELIVE_ENDPOINT=https://zimax.services.ai.azure.com
AZURE_VOICELIVE_MODEL=gpt-realtime
AZURE_VOICELIVE_VOICE=en-US-Ava:DragonHDLatestNeural

# Chat - Production gateway with premium tier
AZURE_AI_ENDPOINT=https://zimax-gw.azure-api.net/zimax/openai/v1
AZURE_AI_DEPLOYMENT=gpt-5.1-chat

# Production database
DATABASE_URL=postgresql://prod_user@prod-postgres/engram_prod

# Compliance
AUDIT_LOG_ENABLED=true
DATA_RETENTION_DAYS=90
```

### 6.3 Authentication
```bash
# Entra ID production tenant
# MFA enforced
# Conditional Access policies applied

# Required security
- MFA for all users
- Compliant device required
- Geographic restrictions (optional)
- Session timeout: 8 hours
```

### 6.4 Azure Resources
| Resource | Name | Configuration |
|----------|------|---------------|
| Container App | prod-env-api | 1 vCPU, 2GB RAM, scale 1-10, zone redundant |
| AI Services | zimax | Premium tier, 100K TPM |
| PostgreSQL | prod-postgres | General Purpose, HA, geo-backup |
| Key Vault | prodenvkv* | HSM-backed keys |
| Private Link | All services | No public endpoints |

### 6.5 Operational Procedures

#### Production Deployment
```bash
# Requires approval gate
gh workflow run deploy.yml -f environment=production

# Blue-green deployment
# 1. Deploy to staging slot
# 2. Run smoke tests
# 3. Swap slots
# 4. Monitor for 15 minutes
# 5. Rollback if issues
```

#### Rollback Procedure
```bash
# Immediate rollback
az containerapp revision activate \
  --name prod-env-api \
  --resource-group engram-rg-prod \
  --revision <previous-revision>

# Verify rollback
curl https://prod-env-api.../health
```

#### Incident Response
```markdown
## VoiceLive Incident
1. Check Azure AI Services status
2. Review Container App logs
3. Check network connectivity
4. Verify Managed Identity permissions
5. Escalate to Azure Support if needed

## Chat Incident
1. Check APIM gateway status
2. Verify API key in Key Vault
3. Check rate limiting
4. Review error logs
5. Escalate if persistent
```

### 6.6 Monitoring & Alerting

```yaml
# Alert Rules
- name: VoiceLive Error Rate
  condition: error_rate > 5%
  severity: High
  action: PagerDuty + Slack

- name: Chat Latency
  condition: p95_latency > 3s
  severity: Medium
  action: Slack

- name: Active Sessions Spike
  condition: sessions > 100
  severity: Low
  action: Email

- name: Authentication Failures
  condition: auth_failures > 10/min
  severity: High
  action: PagerDuty + Security Team
```

### 6.7 Compliance

```markdown
## Audit Requirements
- All API calls logged with user identity
- Voice recordings retained per policy
- Chat transcripts encrypted at rest
- Monthly access reviews
- Quarterly penetration testing

## Data Handling
- PII masked in logs
- No sensitive data in error messages
- GDPR right to erasure supported
- Data residency: East US 2
```

---

## 7. Environment Comparison Matrix

| Feature | Staging POC | Dev | Test | UAT | Prod |
|---------|-------------|-----|------|-----|------|
| **Auth** | Dev tokens | Dev tokens | Service Principal | Entra ID | Entra ID + MFA |
| **VoiceLive** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Chat** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Managed Identity** | ✅ | ❌ (local) | ✅ | ✅ | ✅ |
| **Private Link** | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Audit Logging** | ❌ | ❌ | ✅ | ✅ | ✅ |
| **HA/DR** | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Scale Min** | 0 | 0 | 0 | 1 | 1 |
| **Scale Max** | 3 | 2 | 2 | 5 | 10 |
| **Cost/Month** | ~$50 | ~$30 | ~$40 | ~$100 | ~$500+ |

---

## 8. Secrets Management

### 8.1 GitHub Secrets (CI/CD)
```bash
# Required for all environments
AZURE_CREDENTIALS          # Service Principal JSON
CR_PAT                     # Container Registry token

# Per-environment
AZURE_AI_ENDPOINT          # AI Services endpoint
AZURE_OPENAI_KEY           # APIM API key
POSTGRES_PASSWORD          # Database password
```

### 8.2 Key Vault Secrets
```bash
# Staging POC
azure-ai-key               # AI Services key
zep-api-key                # Memory service key

# Production (additional)
encryption-key             # Data encryption
audit-storage-key          # Audit log storage
```

### 8.3 Rotation Schedule
| Secret | Rotation | Procedure |
|--------|----------|-----------|
| API Keys | 90 days | Automated via Key Vault |
| DB Password | 180 days | Manual with downtime window |
| Service Principal | 365 days | Create new, update, delete old |

---

## 9. Troubleshooting Guide

### 9.1 VoiceLive Issues

| Symptom | Cause | Resolution |
|---------|-------|------------|
| `voicelive_configured: false` | Missing endpoint | Set `AZURE_VOICELIVE_ENDPOINT` |
| 401 Unauthorized | Invalid credential | Check Managed Identity / Key Vault |
| WebSocket disconnect | Network timeout | Increase client timeout, check firewall |
| Audio quality poor | Codec mismatch | Ensure PCM16, 24kHz, mono |

### 9.2 Chat Issues

| Symptom | Cause | Resolution |
|---------|-------|------------|
| 401 Missing token | No auth header | Add `Authorization: Bearer <token>` |
| 429 Rate limited | Too many requests | Implement backoff, check quota |
| Slow responses | Model latency | Check Azure AI status, consider caching |
| Empty responses | Context too long | Reduce conversation history |

### 9.3 Common Commands

```bash
# Check container logs
az containerapp logs show --name staging-env-api --resource-group engram-rg --tail 100

# Restart container
az containerapp revision restart --name staging-env-api --resource-group engram-rg --revision <rev>

# Check env vars
az containerapp show --name staging-env-api --resource-group engram-rg \
  --query "properties.template.containers[0].env"

# Test health
curl https://<api-url>/health | jq
curl https://<api-url>/api/v1/voice/status | jq
```

---

## 10. Appendix

### 10.1 API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | None | Health check |
| `/api/v1/voice/status` | GET | None | VoiceLive status |
| `/api/v1/voice/config/{agent}` | GET | None | Agent voice config |
| `/api/v1/voice/ws` | WS | Token | Voice WebSocket |
| `/api/v1/chat` | POST | Token | Chat message |
| `/api/v1/agents` | GET | None | List agents |

### 10.2 Voice WebSocket Protocol

```json
// Client -> Server
{"type": "init", "session_id": "...", "agent_id": "elena"}
{"type": "audio", "data": "<base64-pcm16>"}
{"type": "switch_agent", "agent_id": "marcus"}
{"type": "end"}

// Server -> Client
{"type": "ready", "session_id": "...", "agent": {...}}
{"type": "transcription", "status": "listening|processing|complete", "text": "..."}
{"type": "audio", "data": "<base64-pcm16>"}
{"type": "agent_switched", "agent_id": "marcus"}
{"type": "error", "message": "..."}
```

### 10.3 Contact & Escalation

| Level | Contact | Response Time |
|-------|---------|---------------|
| L1 | DevOps Team | < 15 min |
| L2 | Platform Engineering | < 1 hour |
| L3 | Azure Support | < 4 hours |
| Security | Security Team | Immediate |

---

*Document maintained by Platform Engineering. For updates, submit PR to `docs/sop-voicelive-chat-environments.md`*
