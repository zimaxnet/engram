---
layout: default
title: Engram Platform Pricing & Deployment Levels
---

# Engram Platform Pricing & Deployment Levels

## Executive Summary

This document provides comprehensive pricing estimates for **five deployment levels** of the Engram platform, from a cost-optimized **Staging POC** with Azure Container Apps (scale-to-zero) to a fully supported **Enterprise Production** deployment with Kubernetes. All pricing is based on Azure public pricing as of 2024 and includes Infrastructure as Code (IAC) deployment strategies for customer Azure tenants.

**Current Deployment**: Staging POC with ACA (scale-to-zero) and PostgreSQL B1ms SKU (~$23/month idle, ~$50-80/month light usage).

---

## Deployment Level Overview

| Level | Environment | Compute | Database | Storage | Support | Est. Monthly Cost |
|-------|-----------|---------|----------|---------|---------|-------------------|
| **Level 1** | Staging POC | ACA (scale-to-zero) | PostgreSQL B1ms | Blob Storage (LRS) | Self-service | $23-80 |
| **Level 2** | Development | Kubernetes (2 nodes) | PostgreSQL B1ms | Blob Storage (LRS) | Business hours | $200-400 |
| **Level 3** | Test | Kubernetes (3 nodes) | PostgreSQL D2s_v3 | Blob Storage (ZRS) | Business hours | $500-800 |
| **Level 4** | UAT | Kubernetes (4 nodes) | PostgreSQL D4s_v3 (HA) | Blob Storage (GRS) | Extended hours | $1,200-2,000 |
| **Level 5** | Production | Kubernetes (6+ nodes) | PostgreSQL D8s_v3 (HA) | Blob Storage (GZRS) | 24/7 support | $3,000-5,000 |

---

## Level 1: Staging POC (Current Deployment)

### Description

**Purpose**: Initial proof-of-concept, testing, and validation. Minimal cost with scale-to-zero capabilities.

**Architecture**:
- **Compute**: Azure Container Apps (Consumption plan, scale-to-zero)
- **Database**: Azure Database for PostgreSQL Flexible Server (B1ms - Burstable)
- **Storage**: Azure Blob Storage (Standard, LRS, Hot tier)
- **Orchestration**: Temporal OSS (deployed in ACA)
- **Memory**: Zep OSS (deployed in ACA)
- **ETL**: Unstructured OSS (integrated in FastAPI)
- **UI**: Azure Static Web Apps

### Infrastructure Components

| Component | Configuration | Purpose |
|-----------|--------------|---------|
| **Container Apps Environment** | Consumption plan | Hosts all containerized services |
| **Backend API** | 0-10 replicas, 0.5 vCPU, 1GB RAM | FastAPI backend with Unstructured |
| **Worker** | 0-5 replicas, 0.5 vCPU, 1GB RAM | Temporal workflow workers |
| **Temporal Server** | 0-3 replicas, 0.5 vCPU, 1GB RAM | Temporal OSS (durable spine) |
| **Temporal UI** | 0-2 replicas, 0.25 vCPU, 0.5GB RAM | Temporal web UI |
| **Zep API** | 0-3 replicas, 0.5 vCPU, 1GB RAM | Zep OSS (memory layer) |
| **PostgreSQL** | B1ms (1 vCore, 2GB RAM, 32GB storage) | Temporal + Zep storage |
| **Blob Storage** | Standard LRS, Hot tier | Document storage (System of Record) |
| **Static Web Apps** | Standard tier | Navigation UI frontend |
| **Key Vault** | Standard tier | Secrets management |
| **Log Analytics** | PerGB2018, 30-day retention | Monitoring and logging |

### Pricing Breakdown

#### Infrastructure Costs (Idle - Scale-to-Zero)

| Service | Configuration | Monthly Cost (Idle) | Notes |
|---------|--------------|---------------------|-------|
| **Container Apps** | Scale-to-zero (0 replicas) | $0 | No cost when idle |
| **PostgreSQL B1ms** | 1 vCore, 2GB RAM, 32GB storage | $13 | Always-on (required for Temporal) |
| **Blob Storage** | ~10GB, Standard LRS, Hot tier | $0.18 | Minimal storage |
| **Static Web Apps** | Standard tier | $9 | Always-on hosting |
| **Key Vault** | Standard tier, <10K operations | $0.03 | Minimal operations |
| **Log Analytics** | ~5GB/month, 30-day retention | $0.50 | Basic logging |
| **Total (Idle)** | | **~$23/month** | |

#### Infrastructure Costs (Light Usage - 100 conversations/day)

| Service | Usage | Monthly Cost | Notes |
|---------|-------|--------------|-------|
| **Container Apps** | ~50K vCPU-seconds, ~100K GiB-seconds, ~300K requests | $5 | Scale-to-zero when idle |
| **PostgreSQL B1ms** | Always-on | $13 | Baseline |
| **Blob Storage** | ~50GB, ~10K transactions | $1 | Document storage |
| **Static Web Apps** | Always-on | $9 | Frontend hosting |
| **Key Vault** | ~50K operations | $0.15 | Secret access |
| **Log Analytics** | ~20GB/month | $2 | Application logs |
| **AI Services (Foundry)** | ~1M tokens (input), ~2M tokens (output) | $35 | gpt-4o-mini for simple queries |
| **Total (Light Usage)** | | **~$65/month** | |

#### Infrastructure Costs (Medium Usage - 1,000 conversations/day)

| Service | Usage | Monthly Cost | Notes |
|---------|-------|--------------|-------|
| **Container Apps** | ~500K vCPU-seconds, ~1M GiB-seconds, ~3M requests | $50 | Higher utilization |
| **PostgreSQL B1ms** | Always-on | $13 | May need upgrade |
| **Blob Storage** | ~200GB, ~100K transactions | $4 | More documents |
| **Static Web Apps** | Always-on | $9 | Frontend hosting |
| **Key Vault** | ~500K operations | $1.50 | More secret access |
| **Log Analytics** | ~100GB/month | $10 | More logging |
| **AI Services (Foundry)** | ~10M tokens (input), ~20M tokens (output) | $350 | Mix of gpt-4o-mini and gpt-4o |
| **Total (Medium Usage)** | | **~$438/month** | |

### IAC Deployment

**Location**: `infra/environments/staging/`

**Files**:
- `main.bicep` - Main infrastructure template (current)
- `parameters.json` - Environment-specific parameters
- `modules/` - Reusable Bicep modules

**Deployment Command**:
```bash
az deployment group create \
  --resource-group rg-engram-staging \
  --template-file infra/environments/staging/main.bicep \
  --parameters @infra/environments/staging/parameters.json
```

**Key Parameters**:
```json
{
  "environment": "staging",
  "envName": "engram-staging",
  "postgresSku": "B1ms",
  "enablePrivateLink": false,
  "scaleToZero": true
}
```

---

## Level 2: Development Environment

### Description

**Purpose**: Ongoing development, integration testing, CI/CD pipelines. Stable environment for developers.

**Architecture**:
- **Compute**: Azure Kubernetes Service (AKS) - 2 node pool
- **Database**: Azure Database for PostgreSQL Flexible Server (B1ms)
- **Storage**: Azure Blob Storage (Standard, LRS, Hot tier)
- **Orchestration**: Temporal OSS (Kubernetes deployment)
- **Memory**: Zep OSS (Kubernetes deployment)
- **ETL**: Unstructured OSS (integrated in FastAPI)
- **UI**: Azure Static Web Apps

### Infrastructure Components

| Component | Configuration | Purpose |
|-----------|--------------|---------|
| **AKS Cluster** | 2 nodes (Standard_D2s_v3), System + User node pools | Container orchestration |
| **Temporal OSS** | 2 replicas (server), 1 replica (UI) | Workflow orchestration |
| **Zep OSS** | 2 replicas | Memory layer |
| **Backend API** | 1-3 replicas | FastAPI backend |
| **Worker** | 1-2 replicas | Temporal workers |
| **PostgreSQL** | B1ms (1 vCore, 2GB RAM, 32GB storage) | Temporal + Zep storage |
| **Blob Storage** | Standard LRS, Hot tier | Document storage |
| **Static Web Apps** | Standard tier | Navigation UI |
| **Key Vault** | Standard tier | Secrets management |
| **Log Analytics** | PerGB2018, 30-day retention | Monitoring |

### Pricing Breakdown

| Service | Configuration | Monthly Cost | Notes |
|---------|--------------|--------------|-------|
| **AKS Control Plane** | Free tier | $0 | Free (Standard tier) |
| **AKS Nodes** | 2x Standard_D2s_v3 (2 vCPU, 8GB RAM each) | $144 | $0.20/hour per node |
| **Temporal OSS** | 2 server + 1 UI replicas | $0 | Included in AKS nodes |
| **Zep OSS** | 2 replicas | $0 | Included in AKS nodes |
| **Backend API** | 1-3 replicas | $0 | Included in AKS nodes |
| **Worker** | 1-2 replicas | $0 | Included in AKS nodes |
| **PostgreSQL B1ms** | 1 vCore, 2GB RAM, 32GB storage | $13 | Baseline |
| **Blob Storage** | ~100GB, Standard LRS | $2 | Development data |
| **Static Web Apps** | Standard tier | $9 | Frontend hosting |
| **Key Vault** | Standard tier | $0.15 | Secret management |
| **Log Analytics** | ~50GB/month | $5 | Application logs |
| **Load Balancer** | Standard tier | $18 | AKS load balancer |
| **Public IP** | Standard tier | $3 | Load balancer IP |
| **AI Services (Foundry)** | ~5M tokens/month | $150 | Development usage |
| **Total (Dev)** | | **~$344/month** | + support costs |

### IAC Deployment

**Location**: `infra/environments/dev/`

**Files**:
- `main.bicep` - Main infrastructure template
- `aks-cluster.bicep` - AKS cluster configuration
- `temporal-helm-values.yaml` - Temporal Helm chart values
- `zep-helm-values.yaml` - Zep Helm chart values
- `parameters.json` - Environment-specific parameters

**Deployment Command**:
```bash
# Deploy infrastructure
az deployment group create \
  --resource-group rg-engram-dev \
  --template-file infra/environments/dev/main.bicep \
  --parameters @infra/environments/dev/parameters.json

# Deploy Temporal via Helm
helm install temporal temporalio/temporal \
  --namespace engram \
  --values infra/environments/dev/temporal-helm-values.yaml

# Deploy Zep via Helm
helm install zep zep/zep \
  --namespace engram \
  --values infra/environments/dev/zep-helm-values.yaml
```

**Key Parameters**:
```json
{
  "environment": "dev",
  "envName": "engram-dev",
  "aksNodeCount": 2,
  "aksNodeSize": "Standard_D2s_v3",
  "postgresSku": "B1ms",
  "enablePrivateLink": false
}
```

---

## Level 3: Test Environment

### Description

**Purpose**: Pre-production testing, load testing, integration validation. Production-like configuration.

**Architecture**:
- **Compute**: Azure Kubernetes Service (AKS) - 3 node pool
- **Database**: Azure Database for PostgreSQL Flexible Server (D2s_v3 - General Purpose)
- **Storage**: Azure Blob Storage (Standard, ZRS, Hot tier)
- **Orchestration**: Temporal OSS (Kubernetes, HA)
- **Memory**: Zep OSS (Kubernetes, HA)
- **ETL**: Unstructured OSS (integrated in FastAPI)
- **UI**: Azure Static Web Apps

### Infrastructure Components

| Component | Configuration | Purpose |
|-----------|--------------|---------|
| **AKS Cluster** | 3 nodes (Standard_D2s_v3), System + User node pools | Container orchestration |
| **Temporal OSS** | 3 replicas (server), 2 replicas (UI) | HA workflow orchestration |
| **Zep OSS** | 3 replicas | HA memory layer |
| **Backend API** | 2-5 replicas | FastAPI backend |
| **Worker** | 2-4 replicas | Temporal workers |
| **PostgreSQL** | D2s_v3 (2 vCore, 8GB RAM, 64GB storage) | Temporal + Zep storage |
| **Blob Storage** | Standard ZRS, Hot tier | Document storage (zone-redundant) |
| **Static Web Apps** | Standard tier | Navigation UI |
| **Key Vault** | Standard tier | Secrets management |
| **Log Analytics** | PerGB2018, 30-day retention | Monitoring |

### Pricing Breakdown

| Service | Configuration | Monthly Cost | Notes |
|---------|--------------|--------------|-------|
| **AKS Control Plane** | Free tier | $0 | Free (Standard tier) |
| **AKS Nodes** | 3x Standard_D2s_v3 (2 vCPU, 8GB RAM each) | $216 | $0.20/hour per node |
| **Temporal OSS** | 3 server + 2 UI replicas | $0 | Included in AKS nodes |
| **Zep OSS** | 3 replicas | $0 | Included in AKS nodes |
| **Backend API** | 2-5 replicas | $0 | Included in AKS nodes |
| **Worker** | 2-4 replicas | $0 | Included in AKS nodes |
| **PostgreSQL D2s_v3** | 2 vCore, 8GB RAM, 64GB storage | $72 | General Purpose tier |
| **Blob Storage** | ~500GB, Standard ZRS | $12 | Zone-redundant storage |
| **Static Web Apps** | Standard tier | $9 | Frontend hosting |
| **Key Vault** | Standard tier | $0.30 | Secret management |
| **Log Analytics** | ~200GB/month | $20 | Application logs |
| **Load Balancer** | Standard tier | $18 | AKS load balancer |
| **Public IP** | Standard tier | $3 | Load balancer IP |
| **AI Services (Foundry)** | ~20M tokens/month | $500 | Testing usage |
| **Total (Test)** | | **~$850/month** | + support costs |

### IAC Deployment

**Location**: `infra/environments/test/`

**Files**:
- `main.bicep` - Main infrastructure template
- `aks-cluster.bicep` - AKS cluster configuration (3 nodes)
- `temporal-helm-values.yaml` - Temporal Helm chart values (HA)
- `zep-helm-values.yaml` - Zep Helm chart values (HA)
- `parameters.json` - Environment-specific parameters

**Key Parameters**:
```json
{
  "environment": "test",
  "envName": "engram-test",
  "aksNodeCount": 3,
  "aksNodeSize": "Standard_D2s_v3",
  "postgresSku": "D2s_v3",
  "postgresStorageGB": 64,
  "blobStorageRedundancy": "ZRS",
  "enablePrivateLink": false
}
```

---

## Level 4: UAT Environment

### Description

**Purpose**: User Acceptance Testing, production-like environment, extended support hours.

**Architecture**:
- **Compute**: Azure Kubernetes Service (AKS) - 4 node pool
- **Database**: Azure Database for PostgreSQL Flexible Server (D4s_v3 - General Purpose, HA)
- **Storage**: Azure Blob Storage (Standard, GRS, Hot tier)
- **Orchestration**: Temporal OSS (Kubernetes, HA, history shards configured)
- **Memory**: Zep OSS (Kubernetes, HA, Graphiti optimized)
- **ETL**: Unstructured OSS (integrated in FastAPI)
- **UI**: Azure Static Web Apps
- **Support**: Extended business hours (8am-8pm)

### Infrastructure Components

| Component | Configuration | Purpose |
|-----------|--------------|---------|
| **AKS Cluster** | 4 nodes (Standard_D4s_v3), System + User node pools | Container orchestration |
| **Temporal OSS** | 4 replicas (server), 2 replicas (UI), Codec Server | HA workflow orchestration |
| **Zep OSS** | 4 replicas | HA memory layer |
| **Backend API** | 3-8 replicas | FastAPI backend |
| **Worker** | 3-6 replicas | Temporal workers |
| **PostgreSQL** | D4s_v3 (4 vCore, 16GB RAM, 128GB storage), Zone-Redundant HA | Temporal + Zep storage |
| **Blob Storage** | Standard GRS, Hot tier | Document storage (geo-redundant) |
| **Static Web Apps** | Standard tier | Navigation UI |
| **Key Vault** | Standard tier | Secrets management (CMK) |
| **Log Analytics** | PerGB2018, 90-day retention | Extended retention |
| **Application Insights** | Standard tier | APM and monitoring |

### Pricing Breakdown

| Service | Configuration | Monthly Cost | Notes |
|---------|--------------|--------------|-------|
| **AKS Control Plane** | Free tier | $0 | Free (Standard tier) |
| **AKS Nodes** | 4x Standard_D4s_v3 (4 vCPU, 16GB RAM each) | $576 | $0.40/hour per node |
| **Temporal OSS** | 4 server + 2 UI + Codec Server | $0 | Included in AKS nodes |
| **Zep OSS** | 4 replicas | $0 | Included in AKS nodes |
| **Backend API** | 3-8 replicas | $0 | Included in AKS nodes |
| **Worker** | 3-6 replicas | $0 | Included in AKS nodes |
| **PostgreSQL D4s_v3 (HA)** | 4 vCore, 16GB RAM, 128GB storage, Zone-Redundant | $288 | HA doubles cost |
| **Blob Storage** | ~1TB, Standard GRS | $46 | Geo-redundant storage |
| **Static Web Apps** | Standard tier | $9 | Frontend hosting |
| **Key Vault** | Standard tier | $0.60 | Secret management (CMK) |
| **Log Analytics** | ~500GB/month | $50 | Extended retention |
| **Application Insights** | Standard tier, ~10M data points | $20 | APM monitoring |
| **Load Balancer** | Standard tier | $18 | AKS load balancer |
| **Public IP** | Standard tier | $3 | Load balancer IP |
| **AI Services (Foundry)** | ~50M tokens/month | $1,200 | UAT usage |
| **Zimax Support (Extended)** | 8am-8pm business days | $500 | Extended support |
| **Total (UAT)** | | **~$2,710/month** | |

### IAC Deployment

**Location**: `infra/environments/uat/`

**Files**:
- `main.bicep` - Main infrastructure template
- `aks-cluster.bicep` - AKS cluster configuration (4 nodes, HA)
- `temporal-helm-values.yaml` - Temporal Helm chart values (HA, history shards)
- `zep-helm-values.yaml` - Zep Helm chart values (HA, Graphiti)
- `codec-server-helm-values.yaml` - Codec Server Helm chart values
- `parameters.json` - Environment-specific parameters

**Key Parameters**:
```json
{
  "environment": "uat",
  "envName": "engram-uat",
  "aksNodeCount": 4,
  "aksNodeSize": "Standard_D4s_v3",
  "postgresSku": "D4s_v3",
  "postgresStorageGB": 128,
  "postgresHighAvailability": true,
  "blobStorageRedundancy": "GRS",
  "enablePrivateLink": true,
  "temporalHistoryShards": 16,
  "enableCodecServer": true
}
```

---

## Level 5: Production Environment

### Description

**Purpose**: Fully supported enterprise production deployment with 24/7 support, SLA guarantees, and maximum scalability.

**Architecture**:
- **Compute**: Azure Kubernetes Service (AKS) - 6+ node pool (auto-scaling)
- **Database**: Azure Database for PostgreSQL Flexible Server (D8s_v3 - General Purpose, HA, read replicas)
- **Storage**: Azure Blob Storage (Standard, GZRS, Hot/Cool tier lifecycle)
- **Orchestration**: Temporal OSS (Kubernetes, HA, history shards, Codec Server)
- **Memory**: Zep OSS (Kubernetes, HA, Graphiti optimized, connection pooling)
- **ETL**: Unstructured OSS (integrated in FastAPI, optimized partitioning)
- **UI**: Azure Static Web Apps (CDN, custom domain)
- **Support**: 24/7 support, dedicated resources

### Infrastructure Components

| Component | Configuration | Purpose |
|-----------|--------------|---------|
| **AKS Cluster** | 6+ nodes (Standard_D8s_v3), System + User node pools, auto-scaling | Container orchestration |
| **Temporal OSS** | 6 replicas (server), 3 replicas (UI), Codec Server (HA) | HA workflow orchestration |
| **Zep OSS** | 6 replicas | HA memory layer |
| **Backend API** | 5-15 replicas (auto-scaling) | FastAPI backend |
| **Worker** | 5-12 replicas (auto-scaling) | Temporal workers |
| **PostgreSQL** | D8s_v3 (8 vCore, 32GB RAM, 256GB storage), Zone-Redundant HA, 1 read replica | Temporal + Zep storage |
| **Blob Storage** | Standard GZRS, Hot/Cool tier lifecycle | Document storage (geo-zone-redundant) |
| **Static Web Apps** | Standard tier, CDN | Navigation UI |
| **Key Vault** | Premium tier | Secrets management (CMK, HSM) |
| **Log Analytics** | PerGB2018, 365-day retention | Extended retention |
| **Application Insights** | Standard tier | APM and monitoring |
| **Azure Monitor** | Standard tier | Infrastructure monitoring |
| **Backup** | Azure Backup | Database and storage backups |

### Pricing Breakdown

| Service | Configuration | Monthly Cost | Notes |
|---------|--------------|--------------|-------|
| **AKS Control Plane** | Free tier | $0 | Free (Standard tier) |
| **AKS Nodes** | 6x Standard_D8s_v3 (8 vCPU, 32GB RAM each) | $1,152 | $0.80/hour per node |
| **Temporal OSS** | 6 server + 3 UI + Codec Server (HA) | $0 | Included in AKS nodes |
| **Zep OSS** | 6 replicas | $0 | Included in AKS nodes |
| **Backend API** | 5-15 replicas (auto-scaling) | $0 | Included in AKS nodes |
| **Worker** | 5-12 replicas (auto-scaling) | $0 | Included in AKS nodes |
| **PostgreSQL D8s_v3 (HA)** | 8 vCore, 32GB RAM, 256GB storage, Zone-Redundant | $576 | HA doubles cost |
| **PostgreSQL Read Replica** | D8s_v3 (8 vCore, 32GB RAM) | $288 | Read replica |
| **Blob Storage** | ~5TB, Standard GZRS, Hot/Cool lifecycle | $230 | Geo-zone-redundant storage |
| **Static Web Apps** | Standard tier, CDN | $9 | Frontend hosting |
| **Key Vault Premium** | Premium tier, HSM | $1.50 | Secret management (CMK, HSM) |
| **Log Analytics** | ~2TB/month, 365-day retention | $200 | Extended retention |
| **Application Insights** | Standard tier, ~100M data points | $200 | APM monitoring |
| **Azure Monitor** | Standard tier | $50 | Infrastructure monitoring |
| **Azure Backup** | Database + Storage backups | $100 | Backup and recovery |
| **Load Balancer** | Standard tier | $18 | AKS load balancer |
| **Public IP** | Standard tier | $3 | Load balancer IP |
| **AI Services (Foundry)** | ~200M tokens/month | $4,000 | Production usage |
| **Zimax Support (24/7)** | 24/7 support, dedicated resources | $2,000 | Enterprise support |
| **Total (Production)** | | **~$9,268/month** | Base infrastructure |

**Note**: Production costs vary significantly based on:
- Actual usage (AI tokens, storage, compute)
- Auto-scaling behavior
- Data volume
- Support requirements

### IAC Deployment

**Location**: `infra/environments/prod/`

**Files**:
- `main.bicep` - Main infrastructure template
- `aks-cluster.bicep` - AKS cluster configuration (6+ nodes, auto-scaling)
- `temporal-helm-values.yaml` - Temporal Helm chart values (HA, history shards, Codec Server)
- `zep-helm-values.yaml` - Zep Helm chart values (HA, Graphiti, connection pooling)
- `codec-server-helm-values.yaml` - Codec Server Helm chart values (HA)
- `postgres-ha.bicep` - PostgreSQL HA configuration
- `backup-policy.bicep` - Backup and disaster recovery policies
- `monitoring.bicep` - Monitoring and alerting configuration
- `parameters.json` - Environment-specific parameters

**Key Parameters**:
```json
{
  "environment": "prod",
  "envName": "engram-prod",
  "aksNodeCount": 6,
  "aksNodeMinCount": 6,
  "aksNodeMaxCount": 20,
  "aksNodeSize": "Standard_D8s_v3",
  "postgresSku": "D8s_v3",
  "postgresStorageGB": 256,
  "postgresHighAvailability": true,
  "postgresReadReplicas": 1,
  "blobStorageRedundancy": "GZRS",
  "enablePrivateLink": true,
  "temporalHistoryShards": 32,
  "enableCodecServer": true,
  "codecServerReplicas": 2,
  "logRetentionDays": 365,
  "enableBackup": true,
  "backupRetentionDays": 90
}
```

---

## Cost Optimization Strategies

### Across All Levels

1. **Reserved Capacity**: 1-year or 3-year reservations for PostgreSQL (35-50% savings)
2. **Right-Sizing**: Start conservative, scale based on metrics
3. **Lifecycle Management**: Blob Storage tiering (Hot → Cool → Archive)
4. **Caching**: Application-level caching to reduce database load
5. **Model Selection**: Use gpt-4o-mini for simple queries (30x cheaper)
6. **Auto-Scaling**: Scale down during off-peak hours
7. **Cost Monitoring**: Azure Cost Management + Budget alerts

### Level-Specific Optimizations

**Level 1 (Staging POC)**:
- Scale-to-zero when idle
- Use B1ms PostgreSQL (cheapest)
- Minimal storage

**Level 2-3 (Dev/Test)**:
- Schedule-based scaling (scale down nights/weekends)
- Use development-tier AI models when possible
- Limit log retention (30 days)

**Level 4-5 (UAT/Prod)**:
- Reserved capacity for PostgreSQL
- Blob Storage lifecycle policies (Hot → Cool after 30 days)
- Connection pooling (PgBouncer) to reduce database connections
- CDN for Static Web Apps to reduce egress costs

---

## Support & Operational Costs

### Support Tiers

| Level | Support Hours | Response Time | Monthly Cost |
|-------|--------------|---------------|--------------|
| **Level 1** | Self-service | N/A | $0 |
| **Level 2** | Business hours (9am-5pm) | 4 hours | $200 |
| **Level 3** | Business hours (9am-5pm) | 2 hours | $400 |
| **Level 4** | Extended hours (8am-8pm) | 1 hour | $500 |
| **Level 5** | 24/7 support | 15 minutes | $2,000 |

### Operational Responsibilities

**Zimax Networks LC Provides**:
- Platform deployment and configuration
- Component integration and testing
- Performance optimization
- Monitoring and alerting setup
- Troubleshooting and incident response
- Updates and patches
- Compliance documentation

**Customer Provides**:
- Azure subscription and resource group
- Network configuration (VNet, Private Link)
- Customer-managed encryption keys
- IdP integration (SSO)
- Compliance requirements
- Maintenance windows

---

## IAC Code Structure

### Repository Organization

```
infra/
├── environments/
│   ├── staging/
│   │   ├── main.bicep              # Main infrastructure (current)
│   │   ├── parameters.json         # Staging parameters
│   │   └── README.md               # Deployment instructions
│   ├── dev/
│   │   ├── main.bicep              # Dev infrastructure
│   │   ├── aks-cluster.bicep       # AKS cluster config
│   │   ├── temporal-helm-values.yaml
│   │   ├── zep-helm-values.yaml
│   │   ├── parameters.json
│   │   └── README.md
│   ├── test/
│   │   ├── main.bicep              # Test infrastructure
│   │   ├── aks-cluster.bicep       # AKS cluster config (HA)
│   │   ├── temporal-helm-values.yaml
│   │   ├── zep-helm-values.yaml
│   │   ├── parameters.json
│   │   └── README.md
│   ├── uat/
│   │   ├── main.bicep              # UAT infrastructure
│   │   ├── aks-cluster.bicep       # AKS cluster config (HA)
│   │   ├── temporal-helm-values.yaml
│   │   ├── zep-helm-values.yaml
│   │   ├── codec-server-helm-values.yaml
│   │   ├── parameters.json
│   │   └── README.md
│   └── prod/
│       ├── main.bicep              # Production infrastructure
│       ├── aks-cluster.bicep       # AKS cluster config (HA, auto-scaling)
│       ├── temporal-helm-values.yaml
│       ├── zep-helm-values.yaml
│       ├── codec-server-helm-values.yaml
│       ├── postgres-ha.bicep       # PostgreSQL HA config
│       ├── backup-policy.bicep     # Backup policies
│       ├── monitoring.bicep        # Monitoring config
│       ├── parameters.json
│       └── README.md
├── modules/                        # Reusable Bicep modules (existing)
│   ├── backend-aca.bicep
│   ├── temporal-aca.bicep
│   ├── zep-aca.bicep
│   └── ...
└── helm/                           # Helm chart values
    ├── temporal/
    │   ├── values-staging.yaml
    │   ├── values-dev.yaml
    │   ├── values-test.yaml
    │   ├── values-uat.yaml
    │   └── values-prod.yaml
    ├── zep/
    │   ├── values-staging.yaml
    │   ├── values-dev.yaml
    │   ├── values-test.yaml
    │   ├── values-uat.yaml
    │   └── values-prod.yaml
    └── codec-server/
        ├── values-uat.yaml
        └── values-prod.yaml
```

### Deployment Workflow

1. **Infrastructure Deployment** (Bicep):
   ```bash
   az deployment group create \
     --resource-group rg-engram-{env} \
     --template-file infra/environments/{env}/main.bicep \
     --parameters @infra/environments/{env}/parameters.json
   ```

2. **Kubernetes Setup** (for dev/test/uat/prod):
   ```bash
   az aks get-credentials --resource-group rg-engram-{env} --name aks-engram-{env}
   kubectl create namespace engram
   ```

3. **Temporal Deployment** (Helm):
   ```bash
   helm repo add temporalio https://temporalio.github.io/helm-charts
   helm install temporal temporalio/temporal \
     --namespace engram \
     --values infra/environments/{env}/temporal-helm-values.yaml
   ```

4. **Zep Deployment** (Helm):
   ```bash
   helm repo add zep https://charts.getzep.com
   helm install zep zep/zep \
     --namespace engram \
     --values infra/environments/{env}/zep-helm-values.yaml
   ```

5. **Application Deployment** (for dev/test/uat/prod):
   ```bash
   kubectl apply -f k8s/{env}/backend-deployment.yaml
   kubectl apply -f k8s/{env}/worker-deployment.yaml
   ```

---

## Next Steps

1. **Review this pricing document** with stakeholders
2. **Select deployment level** based on requirements
3. **Prepare customer Azure tenant** (subscription, resource groups, networking)
4. **Deploy infrastructure** using IAC code
5. **Configure monitoring and alerting** for cost tracking
6. **Set up budget alerts** in Azure Cost Management
7. **Schedule regular cost reviews** (monthly)

---

## References

- [Azure Container Apps Pricing](https://azure.microsoft.com/en-us/pricing/details/container-apps/)
- [Azure Kubernetes Service Pricing](https://azure.microsoft.com/en-us/pricing/details/kubernetes-service/)
- [Azure Database for PostgreSQL Pricing](https://azure.microsoft.com/en-us/pricing/details/postgresql/)
- [Azure Blob Storage Pricing](https://azure.microsoft.com/en-us/pricing/details/storage/blobs/)
- [Azure Static Web Apps Pricing](https://azure.microsoft.com/en-us/pricing/details/app-service/static/)
- [Temporal Helm Charts](https://github.com/temporalio/helm-charts)
- [Zep Documentation](https://docs.getzep.com/)

---

**Note**: All pricing is estimated based on Azure public pricing as of 2024. Actual costs may vary based on:
- Regional pricing differences
- Usage patterns
- Reserved capacity discounts
- Enterprise agreements
- Support requirements

For accurate pricing, use the [Azure Pricing Calculator](https://azure.microsoft.com/en-us/pricing/calculator/) with your specific requirements.

