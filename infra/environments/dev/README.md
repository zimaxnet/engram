# Development Environment Deployment

This directory contains the Infrastructure as Code (IAC) for the **Development** environment.

## Overview

- **Environment**: Development
- **Compute**: Azure Kubernetes Service (AKS) - 2 nodes
- **Database**: PostgreSQL B1ms (1 vCore, 2GB RAM, 32GB storage)
- **Storage**: Blob Storage (Standard LRS, Hot tier)
- **Estimated Cost**: ~$200-400/month

## Prerequisites

1. Azure subscription with appropriate permissions
2. Azure CLI installed and configured
3. kubectl installed
4. Helm 3 installed
5. Resource group created: `rg-engram-dev`

## Deployment

### Step 1: Deploy Infrastructure

```bash
az deployment group create \
  --resource-group rg-engram-dev \
  --template-file main.bicep \
  --parameters @parameters.json
```

### Step 2: Get AKS Credentials

```bash
az aks get-credentials \
  --resource-group rg-engram-dev \
  --name aks-engram-dev
```

### Step 3: Create Namespace

```bash
kubectl create namespace engram
```

### Step 4: Deploy Temporal

```bash
helm repo add temporalio https://temporalio.github.io/helm-charts
helm install temporal temporalio/temporal \
  --namespace engram \
  --values temporal-helm-values.yaml
```

### Step 5: Deploy Zep

```bash
helm repo add zep https://charts.getzep.com
helm install zep zep/zep \
  --namespace engram \
  --values zep-helm-values.yaml
```

### Step 6: Deploy Applications

```bash
kubectl apply -f ../../../k8s/dev/backend-deployment.yaml
kubectl apply -f ../../../k8s/dev/worker-deployment.yaml
```

## Configuration

The development environment uses:
- **2 AKS nodes**: Standard_D2s_v3 (2 vCPU, 8GB RAM each)
- **B1ms PostgreSQL**: Cost-optimized for development
- **No Private Link**: Public endpoints
- **30-day log retention**: Basic logging
- **No Codec Server**: Encryption not required for dev

## Cost Optimization

- Schedule-based scaling (scale down nights/weekends)
- Use development-tier AI models when possible
- Limit log retention (30 days)
- Minimal node count (2 nodes)

## Troubleshooting

See the main [infra/README.md](../../README.md) for troubleshooting guidance.

