# Temporal on Azure: Deep Dive Research

> **Date**: December 23, 2025  
> **Status**: Research Complete  
> **Priority**: Critical for Context-as-a-Service Go-to-Market

## Executive Summary

Temporal is essential for durable execution in the Engram Context Engine. Our current Azure Container Apps (ACA) deployment is failing due to gRPC networking issues. This document evaluates three deployment options and provides actionable recommendations.

## Current Problem

```
Worker → Temporal Server: Connection timed out (100.100.x.x:7233)
```

**Root Cause**: Azure Container Apps internal ingress isn't properly routing gRPC traffic to the Temporal Server on port 7233. The transport was set to "Auto" but gRPC requires explicit HTTP/2 configuration.

---

## Deployment Options Comparison

| Criteria | Azure Container Apps | Azure Kubernetes Service | Temporal Cloud |
|----------|---------------------|-------------------------|----------------|
| **Operational Burden** | Medium | High | Low |
| **gRPC Support** | Yes (HTTP/2) | Native | Managed |
| **Cost (Small)** | ~$50-150/mo | ~$200-400/mo | ~$100-200/mo |
| **Cost (Production)** | ~$200-500/mo | ~$500-1500/mo | Consumption-based |
| **Setup Complexity** | Medium | High | Low |
| **Azure Integration** | Native | Native | External (coming) |
| **Private Networking** | VNet Integration | VNet/Private AKS | AWS PrivateLink only* |
| **Time to Production** | Days | Weeks | Hours |

*Azure Private Link support for Temporal Cloud is "coming soon"

---

## Option 1: Fix Azure Container Apps (Current)

### The Issue

ACA's internal ingress uses HTTP-based routing by default. Temporal's gRPC requires proper HTTP/2 transport configuration.

### Required Fixes

1. **Set Transport to HTTP/2** (already attempted):

```bicep
ingress: {
  external: false
  targetPort: 7233
  transport: 'http2'  // Critical for gRPC
  allowInsecure: false
}
```

2. **Verify Internal FQDN Format**:

```bash
# Current (complex internal FQDN)
staging-env-temporal-server.internal.gentleriver-dd0de193.eastus2.azurecontainerapps.io:7233

# Try simpler format (same environment)
staging-env-temporal-server:7233
```

3. **Check Network Connectivity**:

```bash
# From worker container
az containerapp exec --name staging-env-worker --resource-group engram-rg \
  --command "nc -zv staging-env-temporal-server 7233"
```

4. **Consider additionalPortMappings** (ACA 2024+ feature):

```bicep
ingress: {
  targetPort: 7233
  transport: 'http2'
  additionalPortMappings: [
    {
      external: false
      targetPort: 7234  // History gRPC
    }
    {
      external: false
      targetPort: 7235  // Matching gRPC
    }
  ]
}
```

### Pros

- No infrastructure migration needed
- Continue using existing PostgreSQL
- Lower cost for small scale

### Cons

- Networking complexity
- Limited documentation for Temporal on ACA
- May require VNet for reliable internal TCP

### Estimated Effort: 1-2 days

---

## Option 2: Migrate to Azure Kubernetes Service (AKS)

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Azure Kubernetes Service                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │  Temporal   │ │  Temporal   │ │   Engram    │            │
│  │   Server    │ │     UI      │ │   Workers   │            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
│         │              │               │                     │
│         └──────────────┴───────────────┘                     │
│                        │                                     │
│               Cluster IP Service                             │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
              ┌─────────────────┐
              │ Azure PostgreSQL│
              │   (Existing)    │
              └─────────────────┘
```

### Helm Deployment

```bash
# 1. Add Temporal Helm repo
helm repo add temporalio https://temporal.github.io/helm-charts

# 2. Create values-azure.yaml
cat <<EOF > values-azure.yaml
server:
  replicaCount: 3
  config:
    persistence:
      default:
        sql:
          driver: postgres12
          host: staging-env-db.postgres.database.azure.com
          port: 5432
          database: temporal
          user: cogadmin
          password: ${POSTGRES_PASSWORD}
          tls:
            enabled: true
            enableHostVerification: false
  
cassandra:
  enabled: false
  
mysql:
  enabled: false

postgresql:
  enabled: false

elasticsearch:
  enabled: false
  host: ""
EOF

# 3. Deploy
helm install temporal temporalio/temporal \
  -f values-azure.yaml \
  --namespace temporal --create-namespace
```

### Pros

- Native Kubernetes networking (reliable gRPC)
- Helm charts are production-tested
- Better auto-scaling and monitoring
- Strong community support

### Cons

- Higher operational complexity
- Requires Kubernetes expertise
- Higher base cost
- Schema migration required

### Estimated Effort: 3-5 days

---

## Option 3: Temporal Cloud (Managed Service)

### Overview

Temporal Cloud is a fully managed SaaS offering. You only run Workers; Temporal manages everything else.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Azure Environment                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │   Engram    │ │   Engram    │ │   Engram    │            │
│  │   Worker 1  │ │   Worker 2  │ │   Worker N  │            │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘            │
└─────────┼───────────────┼───────────────┼───────────────────┘
          │               │               │
          │   gRPC (TLS)  │               │
          └───────────────┼───────────────┘
                          ▼
          ┌───────────────────────────────┐
          │       Temporal Cloud          │
          │  ┌─────────────────────────┐  │
          │  │   Managed Temporal      │  │
          │  │   - Frontend            │  │
          │  │   - History             │  │
          │  │   - Matching            │  │
          │  │   - Persistence         │  │
          │  └─────────────────────────┘  │
          │  (us-east-2, eu-west-1, etc.) │
          └───────────────────────────────┘
```

### Pricing (Consumption-Based)

- **Essentials Plan**: $100/month minimum
  - Includes 100M Actions + 100GB storage
  - Basic support (business hours)
- **Enterprise Plan**: From $200/month or 7% of consumption
  - Higher SLA, 24/7 support
  - SAML SSO, Audit logs

### Connection Configuration

```python
from temporalio.client import Client, TLSConfig

client = await Client.connect(
    "your-namespace.tmprl.cloud:7233",
    namespace="your-namespace",
    tls=TLSConfig(
        client_cert=open("client.pem", "rb").read(),
        client_private_key=open("client.key", "rb").read(),
    ),
)
```

### Pros

- Zero infrastructure management
- Built-in HA, scaling, disaster recovery
- Expert support from Temporal team
- Fastest time-to-production
- Lower latency (optimized architecture)

### Cons

- External service (data leaves Azure)
- Azure Private Link not yet available
- Ongoing subscription cost
- Less control over infrastructure

### Estimated Effort: 1 day

---

## Recommendation

### Short-Term (1-2 days): Fix ACA Networking

1. **Update TEMPORAL_HOST** to use simplified internal format
2. **Ensure transport: http2** for gRPC
3. **Test with network diagnostics** from worker container
4. **Deploy new revision** after each change

```bash
# Quick fix attempt
az containerapp update --name staging-env-worker --resource-group engram-rg \
  --set-env-vars "TEMPORAL_HOST=staging-env-temporal-server:7233"
```

### Medium-Term (if ACA fails): Evaluate Temporal Cloud

- Sign up for Temporal Cloud trial
- Test connection from Azure to Temporal Cloud
- Compare latency and reliability
- Calculate TCO for expected usage

### Long-Term (Production GTM): Decide Based on Scale

| Scenario | Recommendation |
|----------|----------------|
| POC / MVP | Fix ACA or Temporal Cloud |
| Small Production (<100K workflows/mo) | Temporal Cloud Essentials |
| Large Production (>1M workflows/mo) | AKS Self-Hosted or Temporal Cloud Enterprise |
| Enterprise (compliance requirements) | AKS with VNet isolation |

---

## Immediate Next Steps

1. [ ] Try simplified TEMPORAL_HOST format in worker
2. [ ] Add network debugging tools to worker container
3. [ ] Test direct gRPC connection from worker to Temporal
4. [ ] If ACA fails, create Temporal Cloud trial account
5. [ ] Document findings in `temporal-azure-runbook.md`

---

## References

- [Temporal ACA Deployment Guide](https://learn.temporal.io/getting_started/python/azure_container_apps/)
- [Temporal Helm Charts](https://github.com/temporalio/helm-charts)
- [Temporal Cloud Documentation](https://docs.temporal.io/cloud)
- [Azure Container Apps gRPC Support](https://learn.microsoft.com/en-us/azure/container-apps/grpc)
- [AKS Best Practices](https://learn.microsoft.com/en-us/azure/aks/best-practices)
