---
layout: default
title: "Container Apps Revision Mode: Cost Implications"
parent: "Operations"
---

# Container Apps Revision Mode: Cost Implications

## Overview

Azure Container Apps supports two revision modes:

1. **Single Revision Mode** (Current): Only one active revision at a time
2. **Multiple Revision Mode**: Multiple active revisions with traffic splitting

## Current Configuration

Engram uses **Single Revision Mode** by default. This means:
- Only the latest revision is active
- Previous revisions are automatically deactivated on new deployments
- The same revision number is updated in place (e.g., `0000144` stays `0000144`)

## Cost Implications

### Single Revision Mode (Current)

**Advantages:**
- ✅ **Lower Cost**: Only one set of replicas running at any time
- ✅ **Simpler Management**: No traffic splitting complexity
- ✅ **Scale-to-Zero Compatible**: Idle cost = $0 (when minReplicas = 0)
- ✅ **Predictable Billing**: Single revision = single resource consumption

**Cost Structure:**
- **Resource Consumption**: Billed on vCPU-seconds and GiB-seconds
- **Free Tier**: First 180,000 vCPU-seconds and 360,000 GiB-seconds/month per subscription
- **Idle Cost**: $0 when scaled to zero replicas
- **Active Cost**: Pay only for running replicas (based on actual usage)

**Example Cost (Single Mode):**
```
Scenario: 1,000 conversations/day
- Average: 2 replicas active
- vCPU-seconds: ~2M/month
- GiB-seconds: ~4M/month
- Cost: ~$5-10/month (after free tier)
```

### Multiple Revision Mode

**Disadvantages:**
- ❌ **Higher Cost**: Multiple revisions = multiple sets of replicas
- ❌ **Complex Traffic Management**: Requires traffic splitting configuration
- ❌ **Increased Resource Usage**: All active revisions consume resources
- ❌ **Operational Overhead**: More monitoring and management needed

**Cost Structure:**
- **Resource Consumption**: Each active revision consumes resources independently
- **Traffic Splitting**: 50/50 split = 2x replicas (both revisions active)
- **Gradual Rollout**: 10/90 split = 1.1x replicas (both revisions active)

**Example Cost (Multiple Mode - 50/50 Traffic Split):**
```
Scenario: 1,000 conversations/day, 50/50 traffic split
- Revision A: 2 replicas active
- Revision B: 2 replicas active
- Total: 4 replicas active
- vCPU-seconds: ~4M/month
- GiB-seconds: ~8M/month
- Cost: ~$10-20/month (after free tier)
- **Cost Increase: 2x compared to Single Mode**
```

## Cost Comparison

| Scenario | Single Mode | Multiple Mode (50/50) | Cost Difference |
|----------|-------------|----------------------|-----------------|
| **Idle** (0 replicas) | $0 | $0 | Same |
| **Light** (1 replica) | ~$2-5/month | ~$4-10/month | 2x |
| **Medium** (2 replicas) | ~$5-10/month | ~$10-20/month | 2x |
| **Heavy** (5 replicas) | ~$15-30/month | ~$30-60/month | 2x |

## When to Use Multiple Revision Mode

**Use Multiple Mode Only If:**
- ✅ You need **blue-green deployments** (zero-downtime rollbacks)
- ✅ You need **gradual rollouts** (A/B testing, canary deployments)
- ✅ You need **traffic splitting** (testing new features with subset of users)
- ✅ You have **budget for 2x resource consumption**

**For Engram:**
- ✅ **Single Mode is Optimal**: We use scale-to-zero, so rollbacks are fast
- ✅ **Cost-Conscious**: Single mode aligns with FinOps strategy
- ✅ **Simple Deployments**: FastAPI deployments are lightweight
- ✅ **No Traffic Splitting Needed**: Single active revision is sufficient

## Recommendations

### Current Setup (Single Mode) ✅

**Keep Single Revision Mode** because:
1. **Cost Efficiency**: Only pay for one set of replicas
2. **Scale-to-Zero**: Idle cost = $0 (minReplicas = 0)
3. **Fast Deployments**: Container Apps deployments are quick (~2-5 minutes)
4. **Simple Rollbacks**: Deploy previous image if needed (no traffic splitting)

### If You Need Multiple Mode

**Consider Multiple Mode Only If:**
- You need zero-downtime rollbacks (blue-green)
- You need A/B testing capabilities
- You have budget for 2x resource consumption
- You need gradual feature rollouts

**Cost Impact:**
- **2x resource consumption** during traffic splits
- **Additional monitoring** for multiple revisions
- **Operational complexity** for traffic management

## Cost Optimization Tips

### Single Mode (Current)
1. ✅ **Scale-to-Zero**: minReplicas = 0 (already configured)
2. ✅ **Right-Sizing**: 0.5 vCPU, 1GB RAM per replica (already configured)
3. ✅ **Auto-Scaling**: Max 10 replicas (prevents runaway costs)
4. ✅ **Idle Behavior**: Scales to 0 after 30 minutes idle

### Multiple Mode (If Needed)
1. ⚠️ **Minimize Traffic Splits**: Keep splits short (minutes, not hours)
2. ⚠️ **Monitor Both Revisions**: Track resource usage for both
3. ⚠️ **Quick Rollouts**: Complete rollouts quickly to reduce overlap
4. ⚠️ **Budget Alerts**: Set up alerts for 2x resource consumption

## Monitoring

### Key Metrics to Track

**Single Mode:**
- Active replicas (should be 0 when idle)
- vCPU-seconds per month
- GiB-seconds per month
- Deployment frequency

**Multiple Mode:**
- Active revisions count
- Traffic split percentages
- Resource consumption per revision
- Total resource consumption (sum of all revisions)

### Cost Alerts

Set up Azure Cost Management alerts for:
- Container Apps resource consumption > threshold
- Multiple revisions active for > 1 hour
- Resource consumption spikes

## Conclusion

**Single Revision Mode is the optimal choice for Engram:**

✅ **Cost-Efficient**: Only one set of replicas
✅ **Scale-to-Zero Compatible**: $0 idle cost
✅ **Simple Management**: No traffic splitting complexity
✅ **Fast Deployments**: Quick rollouts and rollbacks
✅ **FinOps Aligned**: Matches our cost-conscious architecture

**Cost Impact of Current Setup:**
- **Idle**: $0 (scales to zero)
- **Light Usage**: ~$2-5/month
- **Medium Usage**: ~$5-10/month
- **Heavy Usage**: ~$15-30/month

**If switching to Multiple Mode:**
- **Cost Increase**: 2x resource consumption during traffic splits
- **Use Case**: Only if blue-green deployments or A/B testing is required
- **Recommendation**: Keep Single Mode unless specific need arises

