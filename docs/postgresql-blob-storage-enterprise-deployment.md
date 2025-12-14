---
layout: default
title: PostgreSQL & Blob Storage Enterprise Deployment Strategy
---

# PostgreSQL & Azure Blob Storage Enterprise Deployment Strategy for Engram Platform

## Executive Summary

This document outlines Zimax Networks LC's strategy for deploying Azure Database for PostgreSQL Flexible Server (with pgvector) and Azure Blob Storage in customer environments (dev/test/UAT/prod). These services form the foundation of Engram's data storage architecture: PostgreSQL serves as the "System of Recall" (Zep memory layer), while Blob Storage serves as the "System of Record" (document artifacts). This plan addresses enterprise requirements including SKU selection, pgvector configuration, Blob Storage tier optimization, customer-managed key encryption, lifecycle management, and NIST AI RMF compliance.

**Key Decision**: Azure Database for PostgreSQL Flexible Server + Azure Blob Storage for customer environments to enable:
- Full control over database sizing and pgvector configuration
- Customer-managed encryption keys (BYOK)
- Data residency in customer-controlled Azure infrastructure
- Cost optimization through right-sizing and tier selection
- Integration with customer's existing Azure infrastructure

---

## 1. PostgreSQL Flexible Server vs Alternatives: Enterprise Comparison

### Service Comparison Matrix

| Feature | Flexible Server (Recommended) | Single Server (Legacy) | Self-Hosted on VM | HorizonDB (Preview) | Engram Requirement |
|---------|-------------------------------|------------------------|-------------------|---------------------|-------------------|
| **Deployment** | Fully managed Azure service | Fully managed (legacy) | Customer-managed VM | Fully managed (preview) | ✅ Required - Managed service |
| **pgvector Support** | Native extension support | Native extension support | Full control | Enhanced vector search | ✅ Required - pgvector essential |
| **SKU Flexibility** | Burstable, General Purpose, Memory Optimized | Limited tiers | Full control | High-performance tiers | ✅ Required - Right-sizing |
| **High Availability** | Zone-redundant (99.99% SLA) | Built-in HA | Customer-managed | Multi-zone replication | ✅ Required - Production HA |
| **Encryption Keys** | Customer-managed keys (CMK) | Azure-managed only | Full control | Customer-managed keys | ✅ **CRITICAL** - CMK required |
| **Storage Scaling** | Independent compute/storage | Coupled | Full control | Auto-scaling storage | ✅ Required - Flexible scaling |
| **Cost Model** | Pay-per-use, reserved capacity | Pay-per-use | Infrastructure costs | Pay-per-use | ✅ Required - Predictable costs |
| **Stop/Start** | Supported (dev/test) | Not supported | Full control | Not supported | ✅ Required - Scale-to-zero |
| **Maintenance Windows** | Customer-controlled | Azure-managed | Customer-controlled | Azure-managed | ✅ Required - Control |
| **Compliance** | SOC 2, HIPAA, PCI-DSS | SOC 2, HIPAA | Customer-managed | SOC 2, HIPAA | ✅ Required - Enterprise compliance |
| **On-Call Support** | Azure support + Zimax Networks LC | Azure support | Zimax Networks LC | Azure support | ✅ Zimax Networks LC provides support |

### Decision Rationale for Flexible Server

**Why Azure Database for PostgreSQL Flexible Server for Customer Environments:**

1. **pgvector Native Support**: Flexible Server provides native support for pgvector extension, essential for Zep's vector similarity search. HorizonDB offers enhanced vector search but is in preview.

2. **Customer-Managed Keys (CMK)**: Required for security assessments. Flexible Server supports CMK via Azure Key Vault, enabling full customer control over encryption keys.

3. **Independent Scaling**: Compute and storage scale independently, allowing cost optimization. Single Server couples compute and storage.

4. **Stop/Start Capability**: For dev/test environments, Flexible Server can be stopped when not in use, reducing costs. Single Server cannot be stopped.

5. **Maintenance Control**: Flexible Server allows customer-controlled maintenance windows, critical for production environments.

6. **Cost Predictability**: Flexible Server offers reserved capacity (up to 55% savings) and predictable pricing vs. self-hosted operational overhead.

7. **High Availability**: Zone-redundant HA with 99.99% SLA meets enterprise requirements without customer-managed failover complexity.

**HorizonDB Consideration**: HorizonDB (preview) offers 3x performance improvement and enhanced vector search. Consider for future migration after GA, but Flexible Server is recommended for current deployments.

---

## 2. PostgreSQL SKU Selection: Critical Sizing Strategy

### The Challenge

PostgreSQL SKU selection is a **critical decision** that affects:
- **Performance**: Insufficient compute leads to query latency and connection pool exhaustion
- **Cost**: Over-provisioning wastes budget; under-provisioning causes performance issues
- **Scalability**: SKU changes require downtime (though Flexible Server supports online scaling)
- **Vector Operations**: pgvector operations are compute-intensive; insufficient resources degrade RAG quality

Unlike Temporal's immutable history shard count, PostgreSQL SKUs can be scaled, but **initial sizing must be accurate** to avoid performance degradation and unnecessary scaling operations.

### SKU Tier Comparison

| Tier | Use Case | vCores | RAM | Cost/Month | Best For |
|------|----------|--------|-----|------------|----------|
| **Burstable (B-series)** | Dev/test, low traffic | 1-2 | 2-4GB | $12-25 | Development, staging POC |
| **General Purpose (D-series)** | Production workloads | 2-64 | 8-256GB | $100-4000+ | Most production use cases |
| **Memory Optimized (E-series)** | High-performance, memory-intensive | 2-64 | 16-512GB | $200-8000+ | Large vector datasets, high concurrency |

### Engram Platform SKU Sizing

| Environment | Expected Load | Recommended SKU | Rationale |
|-------------|---------------|-----------------|-----------|
| **Dev** | 100 sessions, 1K facts | B1ms (1 vCore, 2GB) | Minimal, cost-optimized, can stop/start |
| **Test** | 500 sessions, 10K facts | B2s (2 vCore, 4GB) | Testing load scenarios |
| **UAT** | 2K sessions, 100K facts | D2s_v3 (2 vCore, 8GB) | Production-like load, zone-redundant HA |
| **Production** | 10K+ sessions, 1M+ facts | D4s_v3 (4 vCore, 16GB) or higher | Enterprise scale with headroom |

**Formula Applied (Production)**:
```
Compute Requirements:
- Base: 2 vCores for PostgreSQL operations
- Vector Operations: +1 vCore per 500K vectors (pgvector indexing/search)
- Concurrent Connections: +0.5 vCore per 100 active connections

Memory Requirements:
- Base: 4GB for PostgreSQL
- Vector Indexes: +2GB per 1M vectors (HNSW index memory)
- Connection Pool: +100MB per 10 connections

Production Example:
- 1M vectors → 2 vCores (vector ops) + 2 vCores (base) = 4 vCores
- 1M vectors → 2GB (indexes) + 4GB (base) + 2GB (connections) = 8GB minimum
- Recommended: D4s_v3 (4 vCore, 16GB) for headroom
```

### Storage Sizing Strategy

**Storage Configuration**:
- **Minimum**: 32GB (Flexible Server minimum)
- **Auto-grow**: Enabled (prevents over-provisioning)
- **IOPS**: Scales with storage size (3 IOPS per GB, up to 20,000 IOPS)

**Storage Sizing Formula**:
```
Storage Required = (Data Size + Index Size + WAL + Growth) × Safety Factor

Where:
- Data Size = Episodic + Semantic memory (from Zep sizing)
- Index Size = Vector indexes (HNSW) + B-tree indexes
- WAL = Write-Ahead Log (typically 10-20% of data size)
- Growth = 30-day growth projection
- Safety Factor = 1.5-2.0
```

### Management Strategy

#### 1. Pre-Deployment Assessment

**PostgreSQL Sizing Tool** (to be built):
```python
# tools/postgres-sku-calculator.py
def calculate_postgres_sku(
    expected_sessions: int,
    expected_facts: int,
    expected_concurrent_connections: int,
    growth_factor: float = 2.0
) -> dict:
    """
    Calculate recommended PostgreSQL SKU and storage.
    
    Returns: SKU recommendation, vCores, RAM, storage
    """
    # Calculate compute
    base_vcores = 2
    vector_vcores = math.ceil(expected_facts / 500000)
    connection_vcores = math.ceil(expected_concurrent_connections / 100) * 0.5
    total_vcores = math.ceil((base_vcores + vector_vcores + connection_vcores) * growth_factor)
    
    # Calculate memory
    base_memory_gb = 4
    vector_memory_gb = (expected_facts / 1000000) * 2
    connection_memory_gb = (expected_concurrent_connections / 10) * 0.1
    total_memory_gb = math.ceil((base_memory_gb + vector_memory_gb + connection_memory_gb) * growth_factor)
    
    # Map to Azure SKU
    if total_vcores <= 1 and total_memory_gb <= 2:
        return {"sku": "B1ms", "vcores": 1, "ram_gb": 2, "storage_gb": 32}
    elif total_vcores <= 2 and total_memory_gb <= 8:
        return {"sku": "D2s_v3", "vcores": 2, "ram_gb": 8, "storage_gb": 64}
    elif total_vcores <= 4 and total_memory_gb <= 16:
        return {"sku": "D4s_v3", "vcores": 4, "ram_gb": 16, "storage_gb": 128}
    else:
        return {"sku": "D8s_v3", "vcores": 8, "ram_gb": 32, "storage_gb": 256}
```

#### 2. SKU Scaling Strategy

**Online Scaling** (Flexible Server):
- Compute scaling: Supported with minimal downtime (5-10 minutes)
- Storage scaling: Supported online (no downtime)
- **Recommendation**: Start conservative, scale up based on metrics

**Scaling Triggers**:
- CPU utilization > 70% sustained
- Memory utilization > 80%
- Connection pool > 80% utilization
- Query latency p95 > 500ms

#### 3. Monitoring and Alerting

**Metrics to Track**:
- `postgres_cpu_percent` - Alert if > 70%
- `postgres_memory_percent` - Alert if > 80%
- `postgres_connections_active` - Alert if > 80% of max_connections
- `postgres_storage_percent` - Alert if > 85%
- `postgres_query_duration_p95` - Alert if > 500ms

**Alert Thresholds**:
- **Warning**: CPU > 60%, Memory > 70%, Connections > 70%
- **Critical**: CPU > 80%, Memory > 90%, Connections > 90%, Storage > 90%

---

## 3. Azure Blob Storage Tier Selection: Cost Optimization Strategy

### The Challenge

Azure Blob Storage tier selection directly impacts cost and performance:
- **Hot Tier**: High access costs, low storage costs (frequently accessed data)
- **Cool Tier**: Lower access costs, higher storage costs (infrequently accessed)
- **Archive Tier**: Lowest storage costs, highest retrieval costs (rarely accessed)
- **Immutable Policies**: Once set, cannot be easily changed (compliance requirement)

**Tier selection must be optimized** based on data access patterns to minimize costs while meeting performance requirements.

### Blob Storage Tier Comparison

| Tier | Use Case | Storage Cost/GB | Access Cost/10K | Retrieval Time | Min Retention |
|------|----------|-----------------|-----------------|----------------|---------------|
| **Hot** | Frequently accessed documents | $0.018 | $0.05 | Immediate | None |
| **Cool** | Infrequently accessed (30+ days) | $0.01 | $0.10 | Immediate | 30 days |
| **Archive** | Rarely accessed (180+ days) | $0.002 | $5.00 | 15 hours | 180 days |

### Engram Platform Tier Strategy

**Two-Plane Architecture**:

| Data Plane | Tier Strategy | Rationale |
|------------|--------------|-----------|
| **Record Plane (Blob Storage)** | Hot → Cool → Archive lifecycle | Documents accessed frequently initially, then archived |
| **Recall Plane (PostgreSQL)** | Always Hot (database) | Vector search requires immediate access |

**Lifecycle Policy Configuration**:
```json
{
  "rules": [
    {
      "name": "RecordPlaneLifecycle",
      "enabled": true,
      "type": "Lifecycle",
      "definition": {
        "filters": {
          "blobTypes": ["blockBlob"],
          "prefixMatch": ["record-plane/"]
        },
        "actions": {
          "baseBlob": {
            "tierToCool": {
              "daysAfterModificationGreaterThan": 30
            },
            "tierToArchive": {
              "daysAfterModificationGreaterThan": 90
            },
            "delete": {
              "daysAfterModificationGreaterThan": 2555
            }
          }
        }
      }
    }
  ]
}
```

### Management Strategy

#### 1. Pre-Deployment Assessment

**Blob Storage Sizing Tool** (to be built):
```python
# tools/blob-sizer.py
def calculate_blob_storage_requirements(
    expected_documents_per_month: int,
    avg_document_size_mb: float,
    retention_days: int,
    access_pattern: str  # "frequent", "moderate", "rare"
) -> dict:
    """
    Calculate Blob Storage requirements and tier recommendations.
    
    Returns: Storage size, tier distribution, estimated cost
    """
    total_data_gb = (expected_documents_per_month * avg_document_size_mb * retention_days / 30) / 1024
    
    # Tier distribution based on access pattern
    if access_pattern == "frequent":
        hot_pct, cool_pct, archive_pct = 0.7, 0.2, 0.1
    elif access_pattern == "moderate":
        hot_pct, cool_pct, archive_pct = 0.3, 0.5, 0.2
    else:  # rare
        hot_pct, cool_pct, archive_pct = 0.1, 0.3, 0.6
    
    return {
        "total_storage_gb": total_data_gb,
        "tier_distribution": {
            "hot_gb": total_data_gb * hot_pct,
            "cool_gb": total_data_gb * cool_pct,
            "archive_gb": total_data_gb * archive_pct
        },
        "estimated_monthly_cost": calculate_cost(total_data_gb, hot_pct, cool_pct, archive_pct)
    }
```

#### 2. Lifecycle Management

**Automated Tier Transitions**:
- **Hot → Cool**: After 30 days of no access
- **Cool → Archive**: After 90 days of no access
- **Archive → Delete**: After 7 years (compliance retention)

**Configuration**:
```bicep
// infra/main.bicep
resource lifecyclePolicy 'Microsoft.Storage/storageAccounts/blobServices/lifecyclePolicies@2021-09-01' = {
  parent: blobService
  name: 'default'
  properties: {
    rules: [
      {
        name: 'RecordPlaneLifecycle'
        enabled: true
        type: 'Lifecycle'
        definition: {
          filters: {
            blobTypes: ['blockBlob']
            prefixMatch: ['record-plane/']
          }
          actions: {
            baseBlob: {
              tierToCool: {
                daysAfterModificationGreaterThan: 30
              }
              tierToArchive: {
                daysAfterModificationGreaterThan: 90
              }
            }
          }
        }
      }
    ]
  }
}
```

#### 3. Immutable Storage (Compliance)

**Legal Hold & Immutable Policies**:
- **Legal Hold**: Prevents deletion/modification (compliance requirement)
- **Time-Based Retention**: WORM (Write Once, Read Many) policies
- **Configuration**: Set via Azure Portal or ARM/Bicep

**Use Case**: Documents subject to legal hold or regulatory retention requirements.

---

## 4. Data Encryption: Customer-Managed Keys for Both Services

### NIST AI RMF Alignment

Per [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework), data encryption requirements:

**Govern Function**:
- Establish encryption policies for database and blob storage data
- Define key management responsibilities

**Map Function**:
- Identify sensitive data in PostgreSQL (memory data) and Blob Storage (documents)
- Map encryption requirements to data types

**Measure Function**:
- Verify encryption at rest and in transit
- Audit key rotation and access

**Manage Function**:
- Implement customer-managed key rotation
- Monitor encryption compliance

### Encryption Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Engram Platform                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  PostgreSQL (System of Recall)                           │
│         │                                                │
│         ▼                                                │
│  ┌──────────────────┐                                   │
│  │ PostgreSQL TDE    │ ← Database-level encryption       │
│  │ (Flexible Server) │   - Customer-managed keys        │
│  └──────────────────┘   - Azure Key Vault integration   │
│         │                                                │
│         ▼                                                │
│  ┌──────────────────┐                                   │
│  │ Azure Key Vault  │ ← Customer-managed encryption keys│
│  │ (Customer KMS)   │   - Full control over keys        │
│  └──────────────────┘   - Key rotation capability       │
│                                                          │
│  Azure Blob Storage (System of Record)                  │
│         │                                                │
│         ▼                                                │
│  ┌──────────────────┐                                   │
│  │ Blob Storage TDE  │ ← Storage-level encryption       │
│  │ (Storage Account)│   - Customer-managed keys        │
│  └──────────────────┘   - Azure Key Vault integration   │
│         │                                                │
│         ▼                                                │
│  ┌──────────────────┐                                   │
│  │ Azure Key Vault  │ ← Same customer-managed keys      │
│  │ (Customer KMS)   │   - Unified key management        │
│  └──────────────────┘                                   │
└─────────────────────────────────────────────────────────┘
```

### Implementation Plan

#### Phase 1: PostgreSQL TDE with Customer-Managed Keys

**Azure PostgreSQL Flexible Server TDE**:
- Built-in TDE using Azure Key Vault
- Customer-managed keys (CMK) supported
- Zero application changes required

**Configuration**:
```bicep
// infra/main.bicep
resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2021-06-01' = {
  name: '${prefix}-postgres'
  location: location
  properties: {
    // Enable TDE with customer-managed key
    encryption: {
      type: 'AzureKeyVault'
      keyVaultKeyId: customerKeyVaultKeyId  // Customer's Key Vault key
    }
    // ... other properties
  }
}
```

#### Phase 2: Blob Storage TDE with Customer-Managed Keys

**Azure Blob Storage TDE**:
- Built-in encryption using Azure Key Vault
- Customer-managed keys (CMK) supported
- Applies to all blobs in storage account

**Configuration**:
```bicep
// infra/main.bicep
resource blobStorage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: '${prefix}storage'
  location: location
  properties: {
    // Enable encryption with customer-managed key
    encryption: {
      services: {
        blob: {
          enabled: true
          keyType: 'Account'
        }
      }
      keySource: 'Microsoft.Keyvault'
      keyVaultProperties: {
        keyVaultUri: customerKeyVaultUri
        keyName: customerEncryptionKeyName
        keyVersion: ''  // Use latest version
      }
    }
  }
}
```

#### Phase 3: Unified Key Management

**Single Key Vault for Both Services**:
- Use same customer-managed key for PostgreSQL and Blob Storage
- Simplifies key rotation and management
- Single audit trail for key access

**Key Rotation Strategy**:
1. **PostgreSQL TDE Key Rotation**: Azure PostgreSQL supports online key rotation
2. **Blob Storage Key Rotation**: Update key version in storage account configuration
3. **Dual-Key Support**: Maintain current + previous key during rotation
4. **Automated Rotation**: Scheduled rotation (e.g., quarterly)

---

## 5. Integration Patterns: PostgreSQL + Blob Storage

### Two-Plane Architecture

**System of Record (Blob Storage)**:
- Raw documents (PDF, DOCX, etc.)
- Parsed artifacts from Unstructured
- Provenance metadata
- Access control lists (ACLs)

**System of Recall (PostgreSQL)**:
- Episodic memory (conversation sessions)
- Semantic memory (knowledge graph facts)
- Vector embeddings (for similarity search)
- Entity relationships

### Data Flow

```
Document Upload
     │
     ▼
┌─────────────┐
│ Blob Storage│ ← Store raw document (System of Record)
│  (Record)   │
└─────────────┘
     │
     ▼
┌─────────────┐
│ Unstructured│ ← Process document
│     OSS     │
└─────────────┘
     │
     ├──► Chunks → PostgreSQL (Zep) ← System of Recall
     │              - Vector embeddings
     │              - Facts, entities
     │
     └──► Parsed artifacts → Blob Storage (Record)
                  - Preserve for reprocessing
                  - Compliance/audit
```

### Azure Storage Extension Integration

**PostgreSQL → Blob Storage**:
- Use `azure_storage` extension for data export
- Archive episodic memory to Blob Storage after retention period
- Export backup files to Blob Storage

**Blob Storage → PostgreSQL**:
- Use `azure_storage` extension for data import
- Bulk import historical data
- Restore from backups

---

## 6. NIST AI RMF Compliance Integration

### Framework Mapping

| NIST AI RMF Function | PostgreSQL Implementation | Blob Storage Implementation | Engram Controls |
|----------------------|---------------------------|------------------------------|-----------------|
| **Govern** | Database retention policies, access controls | Blob lifecycle policies, immutable storage | Customer-defined governance |
| **Map** | Data classification (episodic vs. semantic) | Document classification, sensitivity tagging | PII/PHI detection and handling |
| **Measure** | Database performance metrics, query latency | Blob access patterns, tier utilization | Cost, performance, security metrics |
| **Manage** | Database backups, PITR, key rotation | Blob lifecycle management, deletion policies | Data lifecycle management |

### Data Encryption Controls (NIST AI RMF)

**Control ID**: AI-SEC-01 (Data Encryption)

**Implementation**:
1. ✅ **Encryption at Rest**: 
   - PostgreSQL: TDE with customer-managed keys
   - Blob Storage: TDE with customer-managed keys
2. ✅ **Encryption in Transit**: TLS 1.3 for all communications
3. ✅ **Key Management**: Customer-managed keys via Azure Key Vault (unified)
4. ✅ **Key Rotation**: Automated quarterly rotation for both services
5. ✅ **Access Control**: RBAC, Private Endpoints, network isolation

**Evidence**:
- PostgreSQL TDE configuration manifest
- Blob Storage TDE configuration manifest
- Key rotation workflow logs
- Encryption metadata in both services
- Audit logs of key access

### Security Assessment Preparation

**Documentation Required**:
1. **Architecture Diagram**: Show encryption flow (PostgreSQL TDE → Key Vault ← Blob Storage TDE)
2. **Key Management**: Customer KMS integration details
3. **Access Controls**: RBAC, Private Endpoints, audit logging
4. **Compliance Mapping**: NIST AI RMF controls → Engram implementation

**Testing Requirements**:
1. **Encryption Verification**: Verify data is encrypted in both PostgreSQL and Blob Storage
2. **Key Rotation Test**: Simulate unified key rotation without data loss
3. **Access Control Test**: Verify RBAC and Private Endpoints prevent unauthorized access
4. **Audit Logging Test**: Verify all operations are logged

---

## 7. Operational Responsibilities

### Zimax Networks LC Support Model

**For Customer Environments (dev/test/UAT/prod)**:

| Responsibility | Zimax Networks LC | Customer |
|----------------|------------------|----------|
| PostgreSQL deployment | ✅ SKU selection & provisioning | Infrastructure approval |
| pgvector configuration | ✅ Setup & optimization | Database access |
| Blob Storage deployment | ✅ Storage account setup | Infrastructure approval |
| Lifecycle policy configuration | ✅ Tier optimization | Access pattern requirements |
| Encryption setup | ✅ TDE configuration with CMK | Key management |
| Monitoring & alerting | ✅ Setup & maintenance | Alert response |
| Backups & disaster recovery | ✅ Configuration & testing | RPO/RTO requirements |
| Updates & patches | ✅ Planning & execution | Maintenance windows |
| Troubleshooting | ✅ 24/7 support | Issue reporting |
| Compliance documentation | ✅ Preparation | Audit participation |

**Dedicated Resources Required**:
- **PostgreSQL DBA**: SKU sizing, pgvector optimization, performance tuning
- **Storage Engineer**: Blob Storage tier optimization, lifecycle management
- **Security Engineer**: Encryption, compliance, NIST AI RMF
- **SRE**: Monitoring, alerting, incident response

---

## 8. Implementation Roadmap

### Phase 1: Foundation (Months 1-2)
- [ ] Research and document PostgreSQL SKU sizing methodology
- [ ] Build PostgreSQL sizing calculator tool
- [ ] Research and document Blob Storage tier selection strategy
- [ ] Build Blob Storage sizing calculator tool
- [ ] Design unified encryption architecture

### Phase 2: Encryption Implementation (Months 2-3)
- [ ] Configure PostgreSQL TDE with customer-managed keys
- [ ] Configure Blob Storage TDE with customer-managed keys
- [ ] Create unified key rotation workflow
- [ ] Test encryption end-to-end

### Phase 3: Configuration Optimization (Months 3-4)
- [ ] Tune PostgreSQL SKU per environment
- [ ] Configure Blob Storage lifecycle policies
- [ ] Optimize pgvector indexes
- [ ] Document configuration procedures

### Phase 4: Compliance & Documentation (Months 4-5)
- [ ] Map NIST AI RMF controls to implementation
- [ ] Create security assessment documentation
- [ ] Prepare audit evidence
- [ ] Train support team

### Phase 5: Production Deployment (Months 5-6)
- [ ] Deploy to customer dev environment
- [ ] Validate PostgreSQL SKU sizing
- [ ] Validate Blob Storage tier selection
- [ ] Test encryption with customer keys
- [ ] Gradual rollout to test/UAT/prod

---

## 9. Risk Mitigation

### Risk: PostgreSQL Under-Sizing

**Mitigation**:
- Conservative sizing (2x growth factor)
- Monitoring with early warning alerts
- Online SKU scaling (minimal downtime)
- Reserved capacity for predictable workloads

### Risk: Blob Storage Cost Overrun

**Mitigation**:
- Lifecycle policies to automate tier transitions
- Monitoring of tier distribution
- Cost alerts at 50%, 80%, 100% of budget
- Regular cost optimization reviews

### Risk: Encryption Key Compromise

**Mitigation**:
- Unified key rotation workflow
- Dual-key support during rotation
- Audit logging of all key access
- Isolated Key Vault (separate security boundary)

### Risk: Data Loss

**Mitigation**:
- Automated backups (PostgreSQL: PITR, Blob Storage: geo-redundant)
- Regular backup testing
- Disaster recovery procedures
- Immutable storage policies for compliance

---

## 10. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| PostgreSQL CPU utilization | < 70% | Azure Monitor metrics |
| PostgreSQL memory utilization | < 80% | Azure Monitor metrics |
| PostgreSQL connection pool utilization | < 70% | Application metrics |
| Blob Storage cost per GB | < $0.015 (weighted average) | Cost Management API |
| Blob Storage tier distribution | 30% Hot, 50% Cool, 20% Archive | Storage metrics |
| Encryption coverage | 100% of data | Audit logs |
| Key rotation success rate | 100% | Rotation workflow logs |
| Backup success rate | 100% | Backup job logs |
| RPO achievement | 100% | Backup validation |
| Support response time | < 1 hour (P1) | Incident tracking |

---

## 11. Next Steps

1. **Approve this strategy** for customer environment deployment
2. **Allocate resources** for PostgreSQL DBA, Storage Engineer, Security Engineer, SRE
3. **Begin Phase 1** implementation (sizing calculators, tier selection guide)
4. **Engage with customer** infrastructure team for Azure integration requirements
5. **Schedule security assessment** preparation timeline

---

## References

- [Azure Database for PostgreSQL Flexible Server](https://learn.microsoft.com/azure/postgresql/flexible-server/)
- [PostgreSQL pgvector Extension](https://github.com/pgvector/pgvector)
- [Azure Blob Storage Documentation](https://learn.microsoft.com/azure/storage/blobs/)
- [Azure Blob Storage Lifecycle Management](https://learn.microsoft.com/azure/storage/blobs/lifecycle-management-overview)
- [Azure Key Vault Customer-Managed Keys](https://learn.microsoft.com/azure/key-vault/general/customer-managed-keys-overview)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)

