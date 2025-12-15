---
layout: default
title: Zep Enterprise Deployment Strategy
---

# Zep Enterprise Deployment Strategy for Engram Platform

## Executive Summary

This document outlines Zimax Networks LC's strategy for deploying Zep OSS in customer Kubernetes environments (dev/test/UAT/prod). Zep is central to Engram's success as the Memory layer, providing episodic memory (conversation history) and semantic memory (Graphiti knowledge graph). This plan addresses enterprise requirements including PostgreSQL/pgvector configuration, customer-managed key encryption, Graphiti knowledge graph management, and NIST AI RMF compliance.

**Key Decision**: Zep OSS (self-hosted) for customer environments to enable:
- Full control over data encryption with customer-managed keys
- Custom PostgreSQL/pgvector configuration and sizing
- Data residency in customer-controlled infrastructure
- Cost optimization through right-sizing (vs. consumption-based Cloud pricing)
- Integration with customer's existing PostgreSQL infrastructure

---

## 1. Zep OSS vs Zep Cloud: Enterprise Comparison

### Feature Comparison Matrix

| Feature | Zep OSS (Self-Hosted) | Zep Cloud (Managed) | Engram Requirement |
|---------|----------------------|---------------------|-------------------|
| **Deployment** | Self-hosted on customer infrastructure | Fully managed by Zep | ✅ Required - Customer K8s cluster |
| **PostgreSQL Control** | Full control over PostgreSQL/pgvector config | Managed database instances | ✅ Required - Customer-managed PostgreSQL |
| **Data Residency** | Customer-controlled infrastructure | Zep-managed infrastructure | ✅ Required - Customer data residency |
| **Encryption Keys** | Customer-managed keys (BYOK) | Zep-managed or BYOK option | ✅ **CRITICAL** - Customer-managed keys required |
| **Graphiti Configuration** | Full control over knowledge graph settings | Managed configuration | ✅ Required - Custom Graphiti tuning |
| **RBAC/SSO** | Custom implementation | Built-in (Enterprise) | ✅ Required - Customer SSO integration |
| **Compliance** | Customer-managed compliance | SOC 2 Type II, HIPAA included | ✅ Required - Customer-specific compliance |
| **Cost Model** | Infrastructure costs only | Consumption-based pricing | ✅ Required - Predictable costs |
| **BYOM (Bring Your Own Model)** | Full control | Supported | ✅ Required - Customer LLM accounts |
| **Multi-Tenancy** | Custom implementation | Tenant isolation | ✅ Required - Customer-defined isolation |
| **On-Call Support** | Zimax Networks LC team | Zep support team | ✅ Zimax Networks LC provides support |
| **PostgreSQL Sizing** | Customer-controlled sizing | Managed sizing | ✅ **CRITICAL** - Right-sizing for cost optimization |
| **pgvector Configuration** | Full control over vector dimensions/indexes | Managed configuration | ✅ Required - Custom vector tuning |

### Decision Rationale for OSS

**Why Zep OSS for Customer Environments:**

1. **Customer-Managed PostgreSQL**: Engram uses PostgreSQL with pgvector extension. Customers require full control over database sizing, backups, and configuration to meet their infrastructure standards.

2. **Data Residency**: Customer data (conversation history, knowledge graphs, facts) must remain in customer-controlled infrastructure. Zep Cloud stores data in Zep-managed infrastructure.

3. **Cost Predictability**: For enterprise customers with predictable workloads, OSS on customer infrastructure provides cost predictability vs. consumption-based Cloud pricing.

4. **PostgreSQL Integration**: Many customers already have PostgreSQL infrastructure. Zep OSS allows integration with existing databases, reducing operational overhead.

5. **Custom Graphiti Tuning**: Graphiti knowledge graph requires tuning for customer-specific use cases. OSS provides full control over graph configuration, entity extraction, and relationship modeling.

6. **Encryption Control**: Customer-managed keys (BYOK) are required for security assessments. OSS allows full control over encryption via PostgreSQL Transparent Data Encryption (TDE) and application-level encryption.

**Staging POC Exception**: Current ACA deployment is acceptable for testing only. Production requires Kubernetes deployment with customer-managed PostgreSQL.

---

## 2. PostgreSQL/pgvector Configuration: Critical Sizing Strategy

### The Challenge

PostgreSQL with pgvector is the foundation of Zep's memory system. Unlike Temporal's immutable history shard count, PostgreSQL configuration can be changed, but **vector dimension and index type decisions are difficult to reverse**:

- **Vector Dimensions**: Once set, changing dimensions requires re-indexing all vectors (expensive operation)
- **Index Type**: HNSW vs. IVFFlat index choice affects query performance and cannot be easily swapped
- **Connection Pooling**: Must be configured correctly upfront for production workloads
- **Autovacuum Tuning**: Critical for maintaining vector index health

### PostgreSQL Sizing Formula

```
PostgreSQL Capacity = (Episodic Memory + Semantic Memory) × Growth Factor

Where:
- Episodic Memory = Sessions × Avg Messages/Session × Avg Message Size
- Semantic Memory = Facts × Avg Fact Size + Graph Relationships × Overhead
- Growth Factor = 2.0-3.0 (for growth and retention)
```

### Engram Platform PostgreSQL Sizing

| Environment | Expected Load | Recommended SKU | Rationale |
|-------------|---------------|-----------------|-----------|
| **Dev** | 100 sessions, 1K facts | B1ms (1 vCore, 2GB) | Minimal, cost-optimized |
| **Test** | 500 sessions, 10K facts | B2s (2 vCore, 4GB) | Testing load scenarios |
| **UAT** | 2K sessions, 100K facts | D2s_v3 (2 vCore, 8GB) | Production-like load |
| **Production** | 10K+ sessions, 1M+ facts | D4s_v3 (4 vCore, 16GB) or higher | Enterprise scale with headroom |

**Formula Applied (Production)**:
```
10,000 sessions × 50 messages/session × 500 bytes = 250 MB episodic
1,000,000 facts × 1 KB/fact = 1 GB semantic
Total: ~1.25 GB data × 3.0 (growth + indexes) = 3.75 GB
Recommended: D4s_v3 (16GB RAM) for headroom and performance
```

### pgvector Configuration Strategy

#### 1. Vector Dimension Selection

**Decision Point**: Vector dimensions are set at table creation and difficult to change.

**Engram Standard**: 1536 dimensions (OpenAI text-embedding-3-small compatibility)

**Configuration**:
```sql
-- Create vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create memory table with vector column
CREATE TABLE zep_memory_vectors (
    id UUID PRIMARY KEY,
    session_id VARCHAR(255),
    content TEXT,
    embedding vector(1536),  -- IMMUTABLE after creation
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create HNSW index (production)
CREATE INDEX ON zep_memory_vectors 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

**Rationale**:
- **1536 dimensions**: Standard for OpenAI embeddings, compatible with Azure OpenAI
- **HNSW index**: Better query performance than IVFFlat for large datasets
- **m = 16, ef_construction = 64**: Balanced performance vs. index build time

#### 2. Index Type Selection

**HNSW vs. IVFFlat**:

| Index Type | Build Time | Query Performance | Update Cost | Use Case |
|------------|------------|-------------------|-------------|----------|
| **HNSW** | Slow (hours for large datasets) | Excellent (sub-10ms) | High (rebuild required) | Production, read-heavy |
| **IVFFlat** | Fast (minutes) | Good (10-50ms) | Medium (periodic rebuild) | Development, write-heavy |

**Engram Recommendation**: **HNSW for production** (better query performance, acceptable build time)

#### 3. Connection Pooling Configuration

**Critical for Production**: PostgreSQL connection limits must be managed via connection pooling.

**PgBouncer Configuration** (recommended):
```ini
[databases]
zep = host=postgres-server port=5432 dbname=zep

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
reserve_pool_size = 5
```

**Azure PostgreSQL Connection Pooler** (alternative):
- Built-in connection pooler (no PgBouncer required)
- Configure via Azure Portal or ARM/Bicep
- Recommended for Azure-native deployments

#### 4. Autovacuum Tuning

**Critical for Vector Index Health**: Autovacuum maintains index statistics and prevents bloat.

**Production Configuration**:
```sql
-- Enable autovacuum for vector tables
ALTER TABLE zep_memory_vectors SET (
    autovacuum_vacuum_scale_factor = 0.1,
    autovacuum_analyze_scale_factor = 0.05,
    autovacuum_vacuum_cost_delay = 10
);
```

**Monitoring**:
- Track `pg_stat_user_tables` for vacuum activity
- Alert if `n_dead_tup` > 10% of `n_live_tup`
- Monitor index bloat via `pg_stat_user_indexes`

### Management Strategy

#### 1. Pre-Deployment Assessment

**PostgreSQL Sizing Tool** (to be built):
```python
# tools/postgres-sizer.py
def calculate_postgres_sizing(
    expected_sessions: int,
    avg_messages_per_session: int,
    expected_facts: int,
    retention_days: int,
    growth_factor: float = 3.0
) -> dict:
    """
    Calculate recommended PostgreSQL SKU and configuration.
    
    Returns: SKU recommendation, RAM, vCores, storage
    """
    episodic_size_gb = (expected_sessions * avg_messages_per_session * 0.0005) * (retention_days / 30)
    semantic_size_gb = (expected_facts * 0.001)  # 1KB per fact average
    total_data_gb = (episodic_size_gb + semantic_size_gb) * growth_factor
    
    # Map to Azure SKU
    if total_data_gb < 2:
        return {"sku": "B1ms", "vcores": 1, "ram_gb": 2, "storage_gb": 32}
    elif total_data_gb < 10:
        return {"sku": "D2s_v3", "vcores": 2, "ram_gb": 8, "storage_gb": 128}
    else:
        return {"sku": "D4s_v3", "vcores": 4, "ram_gb": 16, "storage_gb": 256}
```

#### 2. Helm Chart Configuration

**values-production.yaml**:
```yaml
postgresql:
  enabled: false  # Use customer's managed PostgreSQL
  external:
    host: "${CUSTOMER_POSTGRES_HOST}"
    port: 5432
    database: "zep"
    user: "zep_user"
    passwordSecret: "customer-postgres-secret"
    sslMode: "require"

zep:
  config:
    database:
      url: "postgresql://zep_user:${PASSWORD}@${CUSTOMER_POSTGRES_HOST}:5432/zep?sslmode=require"
      poolSize: 25
      maxOverflow: 10
    vector:
      dimensions: 1536  # IMMUTABLE after first data ingestion
      indexType: "hnsw"
      indexParams:
        m: 16
        ef_construction: 64
```

#### 3. Monitoring and Alerting

**Metrics to Track**:
- `postgres_connections_active` - Alert if > 80% of max_connections
- `postgres_vector_index_size` - Monitor index growth
- `postgres_autovacuum_lag` - Alert if vacuum falls behind
- `zep_query_latency_p95` - Alert if > 100ms
- `zep_vector_search_hit_rate` - Monitor retrieval quality

**Alert Thresholds**:
- **Warning**: Connection pool > 70% utilization
- **Critical**: Vector index size > 80% of available RAM
- **Warning**: Query latency p95 > 100ms
- **Critical**: Autovacuum lag > 24 hours

#### 4. Migration Strategy (If Under-Sized)

If PostgreSQL is insufficient:
1. **Scale up SKU** (Azure allows online scaling)
2. **Re-index vectors** if dimension change required (downtime)
3. **Migrate to larger instance** using Azure migration tools
4. **Update connection strings** in Zep configuration

**Cost**: SKU scaling is straightforward, but vector re-indexing requires downtime.

---

## 3. Data Encryption: Customer-Managed Keys with PostgreSQL TDE

### NIST AI RMF Alignment

Per [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework), data encryption requirements:

**Govern Function**:
- Establish encryption policies for AI memory data (conversation history, knowledge graphs)
- Define key management responsibilities

**Map Function**:
- Identify sensitive data in memory (PII in conversations, PHI in facts, business secrets)
- Map encryption requirements to memory types (episodic vs. semantic)

**Measure Function**:
- Verify encryption at rest and in transit
- Audit key rotation and access

**Manage Function**:
- Implement customer-managed key rotation
- Monitor encryption compliance

### Zep Encryption Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Engram Platform                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Memory Data (Plaintext)                                │
│  - Episodic: Conversation history                       │
│  - Semantic: Facts, entities, relationships              │
│         │                                                │
│         ▼                                                │
│  ┌──────────────────┐                                   │
│  │ Application-Level │ ← Optional: Field-level encryption│
│  │ Encryption (Zep)  │   - PII/PHI fields only          │
│  └──────────────────┘   - Uses customer KMS             │
│         │                                                │
│         ▼                                                │
│  ┌──────────────────┐                                   │
│  │ PostgreSQL TDE    │ ← Database-level encryption       │
│  │ (Transparent)     │   - All data at rest             │
│  └──────────────────┘   - Customer-managed keys        │
│         │                  (Azure Key Vault)             │
│         ▼                                                │
│  Encrypted Data (PostgreSQL Storage)                    │
│         │                                                │
│         ▼                                                │
│  ┌──────────────────┐                                   │
│  │ Azure Key Vault  │ ← Customer-managed encryption keys│
│  │ (Customer KMS)   │   - Full control over keys        │
│  └──────────────────┘   - Key rotation capability       │
└─────────────────────────────────────────────────────────┘
```

### Implementation Plan

#### Phase 1: PostgreSQL Transparent Data Encryption (TDE)

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
    // ... other properties
    storage: {
      storageSizeGB: 256
    }
    // Enable TDE with customer-managed key
    encryption: {
      type: 'AzureKeyVault'
      keyVaultKeyId: customerKeyVaultKeyId  // Customer's Key Vault key
    }
  }
}
```

#### Phase 2: Application-Level Encryption (Optional)

**For PII/PHI Fields**: Additional encryption for sensitive fields within memory data.

**Location**: `backend/memory/encryption.py`

**Example Implementation**:
```python
# backend/memory/encryption.py
from cryptography.fernet import Fernet
from azure.keyvault.secrets import SecretClient

class MemoryFieldEncryption:
    """
    Encrypts sensitive fields in memory data using customer-managed keys.
    
    Used for:
    - PII in conversation history
    - PHI in facts
    - Business secrets in metadata
    """
    
    def __init__(self, key_vault_url: str, key_name: str):
        self.secret_client = SecretClient(
            vault_url=key_vault_url,
            credential=DefaultAzureCredential()
        )
        self.encryption_key = self._get_encryption_key(key_name)
        self.cipher = Fernet(self.encryption_key)
    
    def encrypt_field(self, field_value: str, field_type: str) -> str:
        """Encrypt a sensitive field before storing in Zep"""
        if field_type in ["pii", "phi", "secret"]:
            return self.cipher.encrypt(field_value.encode()).decode()
        return field_value  # Non-sensitive fields unencrypted
    
    def decrypt_field(self, encrypted_value: str, field_type: str) -> str:
        """Decrypt a sensitive field after retrieving from Zep"""
        if field_type in ["pii", "phi", "secret"]:
            return self.cipher.decrypt(encrypted_value.encode()).decode()
        return encrypted_value
```

#### Phase 3: Key Rotation Strategy

**NIST AI RMF Requirement**: Regular key rotation

**Implementation**:
1. **PostgreSQL TDE Key Rotation**: Azure PostgreSQL supports online key rotation
2. **Application Key Rotation**: Gradual re-encryption of sensitive fields
3. **Dual-Key Support**: Maintain current + previous key during rotation
4. **Automated Rotation**: Scheduled rotation (e.g., quarterly)

**Key Rotation Workflow**:
```python
@workflow.defn
class MemoryEncryptionKeyRotationWorkflow:
    """Rotates encryption keys for all memory data"""
    
    @workflow.run
    async def run(self, new_key_id: str):
        # 1. Rotate PostgreSQL TDE key (Azure-managed)
        # 2. Update application encryption key
        # 3. Gradually re-encrypt sensitive fields
        # 4. Deprecate old key after grace period
        pass
```

---

## 4. Kubernetes Deployment with Helm Charts

### Current State (Staging POC)

**Current**: Zep deployed in Azure Container Apps (ACA)
- `zep-server` Container App
- PostgreSQL backend (Azure Database for PostgreSQL Flexible Server)
- pgvector extension enabled

**Limitation**: ACA doesn't support advanced K8s features needed for enterprise:
- Custom PostgreSQL configuration
- Advanced networking (service mesh)
- Pod security policies
- Resource quotas and limits

### Target State (Customer Environments)

**Deployment**: Zep OSS via Helm Charts (custom or community)

**Architecture**:
```
Kubernetes Cluster (Customer's)
├── Zep Namespace
│   ├── Zep Server (Deployment)
│   │   ├── API Server (3 replicas)
│   │   ├── Memory Service (2 replicas)
│   │   └── Graphiti Service (2 replicas)
│   ├── PgBouncer (Optional, for connection pooling)
│   └── Monitoring (Prometheus exporters)
├── PostgreSQL (Customer's managed database)
│   ├── Azure Database for PostgreSQL Flexible Server
│   │   └── pgvector extension enabled
│   └── OR Customer's on-premises PostgreSQL
└── Monitoring (Prometheus/Grafana)
```

### Helm Chart Customization

**Base Chart**: Custom Helm chart (Zep doesn't provide official Helm charts)

**Custom Values**: `infra/helm/zep/values-production.yaml`

**Key Configuration**:
```yaml
# PostgreSQL connection (customer's database)
zep:
  config:
    database:
      url: "postgresql://zep_user:${PASSWORD}@${CUSTOMER_POSTGRES_HOST}:5432/zep?sslmode=require"
      poolSize: 25
      maxOverflow: 10
      connectionTimeout: 30

# Vector configuration (IMMUTABLE after first ingestion)
vector:
  dimensions: 1536  # Must match embedding model
  indexType: "hnsw"
  indexParams:
    m: 16
    ef_construction: 64
    ef_search: 40

# Graphiti knowledge graph configuration
graphiti:
  enabled: true
  entityExtraction:
    model: "azure-openai"  # Customer's BYOM
    endpoint: "${CUSTOMER_OPENAI_ENDPOINT}"
  relationshipModeling:
    temporalAwareness: true
    maxRelationships: 1000

# Resource sizing
resources:
  api:
    cpu: 1
    memory: 2Gi
  memory:
    cpu: 2
    memory: 4Gi  # Memory service is memory-intensive
  graphiti:
    cpu: 1
    memory: 2Gi

# High availability
replicaCount:
  api: 3
  memory: 2
  graphiti: 2

# Encryption (customer-managed keys)
encryption:
  enabled: true
  keyVaultUrl: "${CUSTOMER_KEY_VAULT_URL}"
  keyName: "${CUSTOMER_ENCRYPTION_KEY_NAME}"
  fieldLevelEncryption:
    enabled: true
    fields: ["pii", "phi", "secret"]
```

### Deployment Process

**Step 1: Pre-Deployment Assessment**
```bash
# Run PostgreSQL sizing calculator
python tools/postgres-sizer.py \
  --sessions 10000 \
  --messages-per-session 50 \
  --facts 1000000 \
  --retention-days 90 \
  --output postgres-recommendation.yaml
```

**Step 2: Configure PostgreSQL**
```bash
# Enable pgvector extension
psql -h ${CUSTOMER_POSTGRES_HOST} -U postgres -d zep \
  -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Create vector tables with correct dimensions
psql -h ${CUSTOMER_POSTGRES_HOST} -U postgres -d zep \
  -f scripts/create-zep-schema.sql
```

**Step 3: Deploy Zep**
```bash
helm install zep ./infra/helm/zep \
  -f values-production.yaml \
  --namespace zep \
  --create-namespace \
  --wait
```

**Step 4: Verify**
```bash
# Check Zep health
kubectl exec -n zep zep-api-0 -- curl http://localhost:8000/health

# Verify PostgreSQL connection
kubectl logs -n zep zep-api-0 | grep "Database connected"

# Verify vector index creation
psql -h ${CUSTOMER_POSTGRES_HOST} -U postgres -d zep \
  -c "SELECT * FROM pg_indexes WHERE tablename = 'zep_memory_vectors';"
```

---

## 5. NIST AI RMF Compliance Integration

### Framework Mapping

| NIST AI RMF Function | Zep Implementation | Engram Controls |
|----------------------|-------------------|-----------------|
| **Govern** | Memory retention policies, data classification | Customer-defined governance |
| **Map** | Memory type classification (episodic vs. semantic) | Sensitivity tagging in metadata |
| **Measure** | Memory quality metrics, retrieval hit rates | Cost, performance, security metrics |
| **Manage** | Memory deletion, GDPR compliance, key rotation | Data lifecycle management |

### Data Encryption Controls (NIST AI RMF)

**Control ID**: AI-SEC-01 (Data Encryption)

**Implementation**:
1. ✅ **Encryption at Rest**: All memory data encrypted via PostgreSQL TDE
2. ✅ **Encryption in Transit**: TLS 1.3 for all PostgreSQL and Zep API communications
3. ✅ **Key Management**: Customer-managed keys via Azure Key Vault
4. ✅ **Key Rotation**: Automated quarterly rotation
5. ✅ **Field-Level Encryption**: Optional encryption for PII/PHI fields

**Evidence**:
- PostgreSQL TDE configuration manifest
- Key rotation workflow logs
- Encryption metadata in memory records
- Audit logs of key access

### Security Assessment Preparation

**Documentation Required**:
1. **Architecture Diagram**: Show encryption flow (Zep → PostgreSQL TDE → Key Vault)
2. **Key Management**: Customer KMS integration details
3. **Access Controls**: RBAC, SSO, audit logging
4. **Compliance Mapping**: NIST AI RMF controls → Engram implementation

**Testing Requirements**:
1. **Encryption Verification**: Verify memory data is encrypted in PostgreSQL
2. **Key Rotation Test**: Simulate key rotation without data loss
3. **Access Control Test**: Verify RBAC prevents unauthorized memory access
4. **Audit Logging Test**: Verify all memory operations are logged

---

## 6. Operational Responsibilities

### Zimax Networks LC Support Model

**For Customer Environments (dev/test/UAT/prod)**:

| Responsibility | Zimax Networks LC | Customer |
|----------------|------------------|----------|
| Zep deployment | ✅ Helm chart deployment | Infrastructure provisioning |
| PostgreSQL sizing | ✅ Assessment & recommendation | Approval & provisioning |
| pgvector configuration | ✅ Setup & optimization | Database access |
| Graphiti tuning | ✅ Configuration & optimization | Use case requirements |
| Monitoring & alerting | ✅ Setup & maintenance | Alert response |
| Updates & patches | ✅ Planning & execution | Maintenance windows |
| Troubleshooting | ✅ 24/7 support | Issue reporting |
| Compliance documentation | ✅ Preparation | Audit participation |

**Dedicated Resources Required**:
- **Zep SME**: Deep expertise in OSS deployment and Graphiti
- **PostgreSQL DBA**: pgvector optimization, performance tuning
- **K8s Engineer**: Helm charts, deployment automation
- **Security Engineer**: Encryption, compliance, NIST AI RMF
- **SRE**: Monitoring, alerting, incident response

---

## 7. Implementation Roadmap

### Phase 1: Foundation (Months 1-2)
- [ ] Research and document PostgreSQL/pgvector sizing methodology
- [ ] Build PostgreSQL sizing calculator tool
- [ ] Create Helm chart for Zep OSS
- [ ] Design Graphiti knowledge graph architecture

### Phase 2: Encryption Implementation (Months 2-3)
- [ ] Configure PostgreSQL TDE with customer-managed keys
- [ ] Implement application-level encryption for PII/PHI
- [ ] Create key rotation workflow
- [ ] Test encryption end-to-end

### Phase 3: Helm Chart Deployment (Months 3-4)
- [ ] Customize Zep Helm chart for enterprise
- [ ] Create deployment automation
- [ ] Test in dev environment
- [ ] Document deployment procedures

### Phase 4: Compliance & Documentation (Months 4-5)
- [ ] Map NIST AI RMF controls to implementation
- [ ] Create security assessment documentation
- [ ] Prepare audit evidence
- [ ] Train support team

### Phase 5: Production Deployment (Months 5-6)
- [ ] Deploy to customer dev environment
- [ ] Validate PostgreSQL sizing
- [ ] Test encryption with customer keys
- [ ] Gradual rollout to test/UAT/prod

---

## 8. Risk Mitigation

### Risk: PostgreSQL Under-Sizing

**Mitigation**:
- Conservative sizing (3x growth factor)
- Monitoring with early warning alerts
- Azure allows online SKU scaling (minimal downtime)

### Risk: Vector Dimension Mismatch

**Mitigation**:
- Standardize on 1536 dimensions (OpenAI compatibility)
- Document dimension requirements upfront
- Re-indexing procedure documented (requires downtime)

### Risk: Encryption Key Compromise

**Mitigation**:
- Key rotation workflow
- Dual-key support during rotation
- Audit logging of all key access
- PostgreSQL TDE with customer-managed keys

### Risk: Graphiti Performance Issues

**Mitigation**:
- Performance testing in UAT
- Graphiti configuration tuning guide
- Monitoring and alerting on query latency
- Index optimization recommendations

---

## 9. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| PostgreSQL connection pool utilization | < 70% | Prometheus metrics |
| Vector search latency p95 | < 100ms | Application metrics |
| Memory retrieval hit rate | > 90% | Zep metrics |
| Encryption coverage | 100% of memory data | Audit logs |
| Key rotation success rate | 100% | Rotation workflow logs |
| Deployment time | < 2 hours | Deployment automation |
| Support response time | < 1 hour (P1) | Incident tracking |

---

## 10. Next Steps

1. **Approve this strategy** for customer environment deployment
2. **Allocate resources** for Zep SME, PostgreSQL DBA, K8s engineer, security engineer
3. **Begin Phase 1** implementation (PostgreSQL sizing calculator, Helm chart research)
4. **Engage with customer** database team for PostgreSQL integration requirements
5. **Schedule security assessment** preparation timeline

---

## References

- [Zep Documentation](https://docs.getzep.com/)
- [Graphiti Knowledge Graph](https://github.com/getzep/graphiti)
- [PostgreSQL pgvector Extension](https://github.com/pgvector/pgvector)
- [Azure Database for PostgreSQL TDE](https://learn.microsoft.com/azure/postgresql/flexible-server/concepts-data-encryption)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)

