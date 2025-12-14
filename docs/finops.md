---
layout: default
title: FinOps Strategy
---

# [Home](/) › FinOps Strategy

# FinOps Strategy

Engram is designed with **cost-conscious architecture** as a first-class concern. This guide details our approach to minimizing and tracking costs while maintaining enterprise-grade capabilities.

## Cost Philosophy

> **"Pay only for what you use, when you use it."**

### Design Principles

1. **Scale-to-Zero**: All compute scales to zero when idle
2. **Right-Sizing**: Match resources to actual workload
3. **Caching**: Reduce redundant API calls
4. **Monitoring**: Track and alert on cost anomalies

---

## Infrastructure Cost Breakdown

### Azure Container Apps (Scale-to-Zero)

| Service | Min Replicas | Max Replicas | vCPU | Memory | Est. Cost/Month |
|---------|--------------|--------------|------|--------|-----------------|
| API | 0 | 10 | 0.5 | 1GB | $0-15* |
| Worker | 0 | 5 | 0.5 | 1GB | $0-10* |
| Frontend | Static | Static | N/A | N/A | $9 |

*Scales to zero when no requests*

### Database & Storage

| Service | Tier | Configuration | Est. Cost/Month |
|---------|------|---------------|-----------------|
| PostgreSQL | B1ms | 1 vCore, 2GB RAM | $13 |
| Storage Account | Standard | LRS, Hot tier | $1 |
| Key Vault | Standard | < 10K operations | $0.03/10K ops |

### AI Services (Foundry)

| Service | Model | Pricing | Notes |
|---------|-------|---------|-------|
| Azure AI (Foundry) | gpt-4o | $5/$15 per 1M tokens | Input/Output |
| Azure AI (Foundry) | gpt-4o-mini | $0.15/$0.60 per 1M tokens | Cost-efficient |

### Estimated Monthly Costs

| Scenario | Description | Est. Cost |
|----------|-------------|-----------|
| **Idle** | No active users | ~$23 |
| **Light** | 100 conversations/day | ~$50-80 |
| **Medium** | 1,000 conversations/day | ~$200-400 |
| **Heavy** | 10,000 conversations/day | ~$1,500-3,000 |

---

## Cost Optimization Strategies

### 1. Model Selection

```python
# Route simple queries to cheaper models
if query_complexity == "simple":
    model = "gpt-4o-mini"  # 30x cheaper
else:
    model = "gpt-4o"
```

**Impact**: 60-80% cost reduction on simple queries

### 2. Memory Caching

```python
# Cache frequently accessed context
@lru_cache(maxsize=1000)
async def get_user_context(user_id: str):
    return await memory_client.get_context(user_id)
```

**Impact**: Reduce memory API calls by 50%+

### 3. Response Streaming

```python
# Stream responses instead of waiting for full completion
async for chunk in agent.stream(message):
    yield chunk
```

**Impact**: Better UX, similar cost, faster perceived response

### 4. Conversation Summarization

```python
# Summarize long conversations to reduce context size
if len(context.episodic.recent_turns) > 10:
    context.episodic.summary = await summarize(context.episodic.recent_turns)
    context.episodic.recent_turns = context.episodic.recent_turns[-3:]
```

**Impact**: 40% token reduction on long conversations

---

## Budget Controls

### Azure Budget Alerts

```bicep
resource budget 'Microsoft.Consumption/budgets@2021-10-01' = {
  name: 'engram-monthly-budget'
  properties: {
    category: 'Cost'
    amount: 500
    timeGrain: 'Monthly'
    notifications: {
      '50percent': {
        enabled: true
        operator: 'GreaterThan'
        threshold: 50
        contactEmails: ['alerts@company.com']
      }
      '80percent': {
        enabled: true
        operator: 'GreaterThan'
        threshold: 80
        contactEmails: ['alerts@company.com']
      }
      '100percent': {
        enabled: true
        operator: 'GreaterThan'
        threshold: 100
        contactEmails: ['alerts@company.com']
      }
    }
  }
}
```

### Application-Level Limits

```python
# Rate limiting per user
RATE_LIMITS = {
    Role.VIEWER: 10,      # 10 requests/minute
    Role.ANALYST: 30,     # 30 requests/minute
    Role.MANAGER: 60,     # 60 requests/minute
    Role.ADMIN: 120,      # 120 requests/minute
}

# Token limits per request
MAX_TOKENS_PER_REQUEST = 4096
MAX_TOKENS_PER_USER_PER_DAY = 100000
```

---

## Cost Tracking

### Metrics Dashboard

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `tokens_used_total` | Total tokens consumed | > 1M/day |
| `api_calls_total` | External API calls | > 10K/day |
| `workflow_executions` | Temporal workflows | > 5K/day |

### Daily Cost Report

```sql
-- Query for daily cost breakdown
SELECT 
  DATE(timestamp) as date,
  agent_id,
  SUM(tokens_input) as input_tokens,
  SUM(tokens_output) as output_tokens,
  SUM(tokens_input * 0.000005 + tokens_output * 0.000015) as estimated_cost
FROM agent_executions
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY DATE(timestamp), agent_id
ORDER BY date DESC;
```

### Cost Attribution

```python
# Tag all resources with cost center
context.operational.metadata = {
    "cost_center": user.department,
    "project": context.operational.workflow_id,
    "agent": context.operational.active_agent,
}
```

---

## Scaling Recommendations

### Development Environment

```yaml
# Minimal resources for dev
api:
  replicas: 0-1
  cpu: 0.25
  memory: 512MB
  
database:
  tier: B1ms  # ~$13/month
```

### Production Environment

```yaml
# Scaled for production
api:
  replicas: 0-10
  cpu: 1.0
  memory: 2GB
  auto_scale:
    min: 0
    max: 10
    target_cpu: 70%
    
database:
  tier: GP_Gen5_2  # ~$150/month
  read_replicas: 1
```

---

## Reserved Capacity

For predictable workloads, consider:

| Service | On-Demand | 1-Year Reserved | 3-Year Reserved |
|---------|-----------|-----------------|-----------------|
| PostgreSQL | $0.034/hr | $0.022/hr (35% off) | $0.017/hr (50% off) |
| Container Apps | Pay-per-use | N/A | N/A |
| Azure AI (Foundry) | Standard | PTU (Provisioned) | PTU |

### When to Use Reserved Capacity

- **PostgreSQL**: Always (predictable baseline)
- **Azure AI PTU**: When > 100K tokens/hour sustained
- **Container Apps**: Never (scale-to-zero is better)

---

## Cost Optimization Checklist

### Infrastructure
- [x] Enable scale-to-zero on all container apps
- [x] Use B1ms PostgreSQL SKU for staging/dev (cost-optimized)
- [ ] Consider reserved capacity for PostgreSQL (35-50% savings)
- [ ] Tag all resources for cost attribution

### Application-Level
- [x] Cache Evidence Telemetry (60s TTL, reduces Monitor API calls by ~95%)
- [x] Paginate BAU artifacts (reduces memory queries by 50-80%)
- [ ] Use gpt-4o-mini for simple queries (30x cheaper)
- [ ] Implement conversation summarization (40% token reduction)
- [ ] Batch Golden Thread runs for bulk operations (30-40% workflow overhead reduction)

### Monitoring & Alerts
- [ ] Set up budget alerts at 50%, 80%, 100%
- [ ] Monitor daily token usage
- [ ] Review monthly cost reports
- [ ] Track Evidence Telemetry cache hit rate (target > 80%)
- [ ] Alert on Golden Thread run failures (indicates waste)

