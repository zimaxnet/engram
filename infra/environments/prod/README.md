# Production Environment Deployment

This directory contains the Infrastructure as Code (IAC) for the **Production** environment.

## Overview

- **Environment**: Production
- **Compute**: Azure Kubernetes Service (AKS) - 6+ nodes (auto-scaling)
- **Database**: PostgreSQL D8s_v3 (8 vCore, 32GB RAM, 256GB storage, HA, read replicas)
- **Storage**: Blob Storage (Standard GZRS, Hot/Cool tier lifecycle)
- **Estimated Cost**: ~$3,000-5,000/month (base infrastructure)

## Prerequisites

1. Azure subscription with appropriate permissions
2. Azure CLI installed and configured
3. kubectl installed
4. Helm 3 installed
5. Resource group created: `rg-engram-prod`
6. Customer-managed encryption keys configured
7. Private Link endpoints configured
8. Network security groups configured

## Deployment

### Step 1: Deploy Infrastructure

```bash
az deployment group create \
  --resource-group rg-engram-prod \
  --template-file main.bicep \
  --parameters @parameters.json
```

### Step 2: Deploy PostgreSQL HA

```bash
az deployment group create \
  --resource-group rg-engram-prod \
  --template-file postgres-ha.bicep \
  --parameters @parameters.json
```

### Step 3: Deploy Backup Policies

```bash
az deployment group create \
  --resource-group rg-engram-prod \
  --template-file backup-policy.bicep \
  --parameters @parameters.json
```

### Step 4: Deploy Monitoring

```bash
az deployment group create \
  --resource-group rg-engram-prod \
  --template-file monitoring.bicep \
  --parameters @parameters.json
```

### Step 5: Get AKS Credentials

```bash
az aks get-credentials \
  --resource-group rg-engram-prod \
  --name aks-engram-prod
```

### Step 6: Create Namespace

```bash
kubectl create namespace engram
```

### Step 7: Deploy Temporal (HA)

```bash
helm repo add temporalio https://temporalio.github.io/helm-charts
helm install temporal temporalio/temporal \
  --namespace engram \
  --values temporal-helm-values.yaml
```

### Step 8: Deploy Zep (HA)

```bash
helm repo add zep https://charts.getzep.com
helm install zep zep/zep \
  --namespace engram \
  --values zep-helm-values.yaml
```

### Step 9: Deploy Codec Server (HA)

```bash
helm install codec-server ./helm/codec-server \
  --namespace engram \
  --values codec-server-helm-values.yaml
```

### Step 10: Deploy Applications

```bash
kubectl apply -f ../../../k8s/prod/backend-deployment.yaml
kubectl apply -f ../../../k8s/prod/worker-deployment.yaml
```

## Configuration

The production environment uses:
- **6+ AKS nodes**: Standard_D8s_v3 (8 vCPU, 32GB RAM each), auto-scaling (6-20 nodes)
- **PostgreSQL D8s_v3 (HA)**: Zone-redundant high availability, 1 read replica
- **Private Link**: All services behind Private Link endpoints
- **365-day log retention**: Extended retention for compliance
- **Codec Server (HA)**: 2 replicas for customer-managed key encryption
- **Backup**: Automated backups with 90-day retention
- **Monitoring**: Application Insights, Azure Monitor, comprehensive alerting

## Security

- **Customer-managed encryption keys**: All data encrypted with customer keys
- **Private Link**: No public endpoints
- **Network security groups**: Restrictive network policies
- **RBAC**: Role-based access control
- **Audit logging**: Comprehensive audit trail

## High Availability

- **AKS**: Multi-zone deployment
- **PostgreSQL**: Zone-redundant HA with read replicas
- **Temporal**: 6 server replicas, 3 UI replicas
- **Zep**: 6 replicas
- **Codec Server**: 2 replicas
- **Applications**: Auto-scaling (5-15 backend, 5-12 worker replicas)

## Cost Optimization

- **Reserved capacity**: 1-year or 3-year reservations for PostgreSQL (35-50% savings)
- **Blob Storage lifecycle**: Hot → Cool tier after 30 days
- **Connection pooling**: PgBouncer to reduce database connections
- **CDN**: Static Web Apps CDN to reduce egress costs
- **Auto-scaling**: Scale down during off-peak hours

## Monitoring

- **Application Insights**: APM and application monitoring
- **Azure Monitor**: Infrastructure monitoring
- **Log Analytics**: 365-day retention
- **Cost Management**: Budget alerts and cost tracking
- **Alerting**: Comprehensive alert rules for all components

## Backup & Disaster Recovery

- **PostgreSQL**: Automated backups with 90-day retention
- **Blob Storage**: Geo-zone-redundant storage (GZRS)
- **Backup policies**: Automated backup schedules
- **RPO/RTO**: 1 hour RPO, 4 hour RTO

## Troubleshooting

See the main [infra/README.md](../../README.md) for troubleshooting guidance.

For production issues, contact 24/7 support.

