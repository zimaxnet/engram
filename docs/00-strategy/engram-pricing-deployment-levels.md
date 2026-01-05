---
layout: default
title: "Deploy infrastructure"
parent: "Strategy"
---





    
        # Engram Platform Pricing & Deployment Levels

        
        
            
## Executive Summary

            This document provides comprehensive pricing estimates for **five deployment levels** of the Engram platform, from a cost-optimized **Staging POC** with Azure Container Apps (scale-to-zero) to a fully supported **Enterprise Production** deployment with Kubernetes. All pricing is based on Azure public pricing as of 2024 and includes Infrastructure as Code (IAC) deployment strategies for customer Azure tenants.


            **Current Deployment**: Staging POC with ACA (scale-to-zero) and PostgreSQL B1ms SKU (~$23/month idle, ~$50-80/month light usage).


        
        
        
## Deployment Level Overview

        
            
                
                    Level
                    Environment
                    Compute
                    Database
                    Storage
                    Support
                    Est. Monthly Cost
                
            
            
                
                    Level 1
                    Staging POC
                    ACA (scale-to-zero)
                    PostgreSQL B1ms
                    Blob Storage (LRS)
                    Self-service
                    **$23-80**
                
                
                    Level 2
                    Development
                    Kubernetes (2 nodes)
                    PostgreSQL B1ms
                    Blob Storage (LRS)
                    Business hours
                    **$200-400**
                
                
                    Level 3
                    Test
                    Kubernetes (3 nodes)
                    PostgreSQL D2s_v3
                    Blob Storage (ZRS)
                    Business hours
                    **$500-800**
                
                
                    Level 4
                    UAT
                    Kubernetes (4 nodes)
                    PostgreSQL D4s_v3 (HA)
                    Blob Storage (GRS)
                    Extended hours
                    **$1,200-2,000**
                
                
                    Level 5
                    Production
                    Kubernetes (6+ nodes)
                    PostgreSQL D8s_v3 (HA)
                    Blob Storage (GZRS)
                    24/7 support
                    **$3,000-5,000**
                
            
        
        
        
## Level 1: Staging POC (Current Deployment)

        
        
### Description

        **Purpose**: Initial proof-of-concept, testing, and validation. Minimal cost with scale-to-zero capabilities.


        
        
#### Architecture

        
            - **Compute**: Azure Container Apps (Consumption plan, scale-to-zero)
            - **Database**: Azure Database for PostgreSQL Flexible Server (B1ms - Burstable)
            - **Storage**: Azure Blob Storage (Standard, LRS, Hot tier)
            - **Orchestration**: Temporal OSS (deployed in ACA)
            - **Memory**: Zep OSS (deployed in ACA)
            - **ETL**: Unstructured OSS (integrated in FastAPI)
            - **UI**: Azure Static Web Apps
        
        
        
            
#### Infrastructure Costs (Idle - Scale-to-Zero)

            
                
                    
                        Service
                        Configuration
                        Monthly Cost (Idle)
                        Notes
                    
                
                
                    
                        **Container Apps**
                        Scale-to-zero (0 replicas)
                        $0
                        No cost when idle
                    
                    
                        **PostgreSQL B1ms**
                        1 vCore, 2GB RAM, 32GB storage
                        $13
                        Always-on (required for Temporal)
                    
                    
                        **Blob Storage**
                        ~10GB, Standard LRS, Hot tier
                        $0.18
                        Minimal storage
                    
                    
                        **Static Web Apps**
                        Standard tier
                        $9
                        Always-on hosting
                    
                    
                        **Key Vault**
                        Standard tier, <10K operations
                        $0.03
                        Minimal operations
                    
                    
                        **Log Analytics**
                        ~5GB/month, 30-day retention
                        $0.50
                        Basic logging
                    
                    
                        **Total (Idle)**
                        
                        **~$23/month**
                        
                    
                
            
        
        
        
            
#### Infrastructure Costs (Light Usage - 100 conversations/day)

            **Total: ~$65/month**


        
        
        
### IAC Deployment

        **Location**: `infra/environments/staging/`


        ```
az deployment group create \
  --resource-group rg-engram-staging \
  --template-file infra/environments/staging/main.bicep \
  --parameters @infra/environments/staging/parameters.json
```
        
        
## Level 2: Development Environment

        
        
### Description

        **Purpose**: Ongoing development, integration testing, CI/CD pipelines. Stable environment for developers.


        
        
            
#### Estimated Monthly Cost: ~$344/month

            Includes: AKS (2 nodes), PostgreSQL B1ms, Blob Storage, Static Web Apps, AI Services, and support costs.


        
        
        
### IAC Deployment

        **Location**: `infra/environments/dev/`


        ```
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
        
        
## Level 3: Test Environment

        
        
### Description

        **Purpose**: Pre-production testing, load testing, integration validation. Production-like configuration.


        
        
            
#### Estimated Monthly Cost: ~$850/month

            Includes: AKS (3 nodes), PostgreSQL D2s_v3, Blob Storage (ZRS), Static Web Apps, AI Services, and support costs.


        
        
        
## Level 4: UAT Environment

        
        
### Description

        **Purpose**: User Acceptance Testing, production-like environment, extended support hours.


        
        
            
#### Estimated Monthly Cost: ~$2,710/month

            Includes: AKS (4 nodes), PostgreSQL D4s_v3 (HA), Blob Storage (GRS), Static Web Apps, AI Services, Codec Server, extended support, and all infrastructure components.


        
        
        
## Level 5: Production Environment

        
        
### Description

        **Purpose**: Fully supported enterprise production deployment with 24/7 support, SLA guarantees, and maximum scalability.


        
        
            
#### Estimated Monthly Cost: ~$9,268/month (Base Infrastructure)

            **Note**: Production costs vary significantly based on actual usage (AI tokens, storage, compute), auto-scaling behavior, data volume, and support requirements.


        
        
        
### Infrastructure Components

        
            - **AKS Cluster**: 6+ nodes (Standard_D8s_v3), System + User node pools, auto-scaling
            - **Temporal OSS**: 6 replicas (server), 3 replicas (UI), Codec Server (HA)
            - **Zep OSS**: 6 replicas
            - **PostgreSQL**: D8s_v3 (8 vCore, 32GB RAM, 256GB storage), Zone-Redundant HA, 1 read replica
            - **Blob Storage**: Standard GZRS, Hot/Cool tier lifecycle
            - **Support**: 24/7 support, dedicated resources
        
        
        
## Cost Optimization Strategies

        
        
            
#### Across All Levels

            
                - **Reserved Capacity**: 1-year or 3-year reservations for PostgreSQL (35-50% savings)
                - **Right-Sizing**: Start conservative, scale based on metrics
                - **Lifecycle Management**: Blob Storage tiering (Hot → Cool → Archive)
                - **Caching**: Application-level caching to reduce database load
                - **Model Selection**: Use gpt-4o-mini for simple queries (30x cheaper)
                - **Auto-Scaling**: Scale down during off-peak hours
                - **Cost Monitoring**: Azure Cost Management + Budget alerts
            
        
        
        
## Support & Operational Costs

        
        
            
#### Support Tiers

            
                
                    
                        Level
                        Support Hours
                        Response Time
                        Monthly Cost
                    
                
                
                    
                        **Level 1**
                        Self-service
                        N/A
                        $0
                    
                    
                        **Level 2**
                        Business hours (9am-5pm)
                        4 hours
                        $200
                    
                    
                        **Level 3**
                        Business hours (9am-5pm)
                        2 hours
                        $400
                    
                    
                        **Level 4**
                        Extended hours (8am-8pm)
                        1 hour
                        $500
                    
                    
                        **Level 5**
                        24/7 support
                        15 minutes
                        $2,000
                    
                
            
        
        
        
## IAC Code Structure

        
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
        
        
## Next Steps

        
            - **Review this pricing document** with stakeholders
            - **Select deployment level** based on requirements
            - **Prepare customer Azure tenant** (subscription, resource groups, networking)
            - **Deploy infrastructure** using IAC code
            - **Configure monitoring and alerting** for cost tracking
            - **Set up budget alerts** in Azure Cost Management
            - **Schedule regular cost reviews** (monthly)
        
        
        
## References

        
            - [Azure Container Apps Pricing](https://azure.microsoft.com/en-us/pricing/details/container-apps/)
            - [Azure Kubernetes Service Pricing](https://azure.microsoft.com/en-us/pricing/details/kubernetes-service/)
            - [Azure Database for PostgreSQL Pricing](https://azure.microsoft.com/en-us/pricing/details/postgresql/)
            - [Azure Blob Storage Pricing](https://azure.microsoft.com/en-us/pricing/details/storage/blobs/)
            - [Azure Static Web Apps Pricing](https://azure.microsoft.com/en-us/pricing/details/app-service/static/)
            - [Temporal Helm Charts](https://github.com/temporalio/helm-charts)
            - [Zep Documentation](https://docs.getzep.com/)
        
        
        **Note**: All pricing is estimated based on Azure public pricing as of 2024. Actual costs may vary based on regional pricing differences, usage patterns, reserved capacity discounts, enterprise agreements, and support requirements.


        For accurate pricing, use the [Azure Pricing Calculator](https://azure.microsoft.com/en-us/pricing/calculator/) with your specific requirements.


    



