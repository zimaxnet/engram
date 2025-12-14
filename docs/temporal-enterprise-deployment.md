---
layout: default
title: Temporal Enterprise Deployment Strategy
---

# Temporal Enterprise Deployment Strategy for Engram Platform

## Executive Summary

This document outlines Zimax Networks LC's strategy for deploying Temporal OSS in customer Kubernetes environments (dev/test/UAT/prod). Temporal is central to Engram's success as the durable execution "Spine" layer, requiring dedicated resources and expertise. This plan addresses enterprise requirements including immutable history shard configuration, customer-managed key encryption, and NIST AI RMF compliance.

**Key Decision**: Temporal OSS (not Cloud) for customer environments to enable:
- Full control over data encryption with customer-managed keys
- Custom RBAC and SSO integration
- Compliance with customer-specific security requirements
- Cost optimization through right-sizing (vs. consumption-based Cloud pricing)

---

## 1. Temporal OSS vs Temporal Cloud: Enterprise Comparison

### Feature Comparison Matrix

| Feature | Temporal OSS (Self-Hosted) | Temporal Cloud | Engram Requirement |
|---------|---------------------------|----------------|-------------------|
| **RBAC** | Custom plugin required | Built-in | ✅ Required - Custom integration with Entra ID |
| **SSO/SAML/SCIM** | Custom implementation | Included in Enterprise | ✅ Required - Customer-specific SSO |
| **Compliance** | Internal implementation (SOC 2, HIPAA) | SOC 2 Type II, HIPAA included | ✅ Required - Customer-specific compliance |
| **Private Link** | Manual setup | Managed | ✅ Required - Customer VNet integration |
| **Service Accounts/API Keys** | Custom implementation | Managed | ✅ Required - Customer-managed keys |
| **Audit Logging** | Custom implementation | Centralized, built-in | ✅ Required - Customer audit requirements |
| **Cloud Availability** | Manual configuration (AWS/GCP/Azure) | Seamless integrations | ✅ Required - Customer's cloud choice |
| **MRN Support** | Complex setup with Replicated Namespaces | Fully managed | ✅ Required - Multi-region for enterprise |
| **On-Call Support** | Zimax Networks LC team | 24x7 Temporal support | ✅ Zimax Networks LC provides support |
| **Data Encryption** | Custom Data Converter + Codec Server | Managed (limited customization) | ✅ **CRITICAL** - Customer-managed keys required |
| **History Shard Count** | Immutable after creation | Managed by Temporal | ✅ **CRITICAL** - Must plan correctly upfront |

### Decision Rationale for OSS

**Why Temporal OSS for Customer Environments:**

1. **Customer-Managed Keys (CMK)**: Required for security assessments. Temporal Cloud's encryption is managed; OSS allows full control via Data Converter + Codec Server.

2. **Custom Compliance**: Customers may require specific compliance frameworks (beyond SOC 2/HIPAA). OSS enables custom audit logging, data residency, and compliance controls.

3. **Cost Predictability**: For enterprise customers with predictable workloads, OSS on customer infrastructure provides cost predictability vs. consumption-based Cloud pricing ($25/1M actions + $200/month base).

4. **Integration Requirements**: Custom RBAC, SSO, and audit logging require OSS flexibility.

5. **Data Residency**: Customer data must remain in customer-controlled infrastructure.

**Staging POC Exception**: Current ACA deployment is acceptable for testing only. Production requires Kubernetes deployment.

---

## 2. History Shard Count: Immutable Configuration Strategy

### The Problem

Temporal's history shard count **cannot be changed after cluster creation**. This requires:
- Over-provisioning for peak demand (wasteful)
- Under-provisioning risks (bottlenecks)
- Careful upfront planning

### Shard Count Sizing Formula

```
Shard Count = (Peak Workflow Throughput / Shard Capacity) × Safety Factor

Where:
- Peak Workflow Throughput = Max workflows/second expected
- Shard Capacity = ~1,000-2,000 workflows/second per shard (conservative)
- Safety Factor = 1.5-2.0 (for growth and spikes)
```

### Engram Platform Shard Sizing

| Environment | Expected Peak Throughput | Recommended Shards | Rationale |
|-------------|-------------------------|-------------------|-----------|
| **Dev** | 10 workflows/sec | 4 shards | Minimal, cost-optimized |
| **Test** | 50 workflows/sec | 8 shards | Testing load scenarios |
| **UAT** | 200 workflows/sec | 16 shards | Production-like load |
| **Production** | 1,000+ workflows/sec | 32-64 shards | Enterprise scale with headroom |

**Formula Applied (Production)**:
```
1,000 workflows/sec ÷ 1,500 workflows/shard = 0.67 shards
0.67 × 2.0 (safety factor) = 1.34 → Round to 32 shards (power of 2)
For enterprise with growth: 64 shards recommended
```

### Management Strategy

#### 1. Pre-Deployment Assessment

**Workload Analysis Tool** (to be built):
```python
# tools/shard-calculator.py
def calculate_shard_count(
    peak_workflows_per_second: int,
    avg_workflow_duration_seconds: int,
    peak_concurrent_workflows: int,
    growth_factor: float = 2.0
) -> int:
    """
    Calculate recommended shard count with growth projection.
    
    Returns: Power-of-2 shard count (4, 8, 16, 32, 64, 128)
    """
    base_shards = (peak_workflows_per_second / 1500) * growth_factor
    return 2 ** math.ceil(math.log2(base_shards))
```

#### 2. Helm Chart Configuration

**values-production.yaml**:
```yaml
server:
  config:
    numHistoryShards: 64  # Immutable - set correctly upfront
    persistence:
      default:
        historyShardCount: 64
```

#### 3. Monitoring and Alerting

**Metrics to Track**:
- `temporal_history_shard_utilization` - Alert if > 80%
- `temporal_workflow_throughput_per_shard` - Alert if > 1,500/sec
- `temporal_shard_hotspots` - Identify uneven distribution

**Alert Thresholds**:
- **Warning**: Any shard > 70% utilization
- **Critical**: Any shard > 90% utilization (indicates need for migration)

#### 4. Migration Strategy (If Under-Provisioned)

If shard count is insufficient:
1. **Create new cluster** with correct shard count
2. **Replicate namespaces** to new cluster (MRN)
3. **Gradual migration** of workflows
4. **Decommission** old cluster

**Cost**: Significant operational overhead. Prevention via proper sizing is critical.

---

## 3. Data Encryption: Customer-Managed Keys with Codec Server

### NIST AI RMF Alignment

Per [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework), data encryption requirements:

**Govern Function**:
- Establish encryption policies for AI workflow data
- Define key management responsibilities

**Map Function**:
- Identify sensitive data in workflow payloads (PII, PHI, business secrets)
- Map encryption requirements to workflow types

**Measure Function**:
- Verify encryption at rest and in transit
- Audit key rotation and access

**Manage Function**:
- Implement customer-managed key rotation
- Monitor encryption compliance

### Temporal Encryption Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Engram Platform                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Workflow Payload (Plaintext)                           │
│         │                                                │
│         ▼                                                │
│  ┌──────────────────┐                                   │
│  │ Data Converter   │ ← Customer-managed encryption     │
│  │ (Client-side)    │   - Uses customer's KMS           │
│  └──────────────────┘   - Azure Key Vault / AWS KMS    │
│         │                  / GCP KMS                     │
│         ▼                                                │
│  Encrypted Payload (Stored in Temporal)                 │
│         │                                                │
│         ▼                                                │
│  ┌──────────────────┐                                   │
│  │ Codec Server     │ ← Decryption service              │
│  │ (Separate Pod)   │   - Isolated from Temporal        │
│  └──────────────────┘   - Customer-managed keys only   │
│         │                                                │
│         ▼                                                │
│  Decrypted Payload (For workflow execution)             │
└─────────────────────────────────────────────────────────┘
```

### Implementation Plan

#### Phase 1: Data Converter (Client-Side Encryption)

**Location**: `backend/workflows/codec/`

**Files to Create**:
- `data_converter.py` - Custom Data Converter with encryption
- `encryption_codec.py` - Payload encryption/decryption
- `key_management.py` - Integration with customer KMS

**Example Implementation**:
```python
# backend/workflows/codec/encryption_codec.py
from temporalio.common import PayloadCodec
from cryptography.fernet import Fernet
from azure.keyvault.secrets import SecretClient

class CustomerManagedKeyCodec(PayloadCodec):
    """
    Encrypts workflow payloads using customer-managed keys.
    
    Integrates with:
    - Azure Key Vault
    - AWS KMS
    - GCP Secret Manager
    """
    
    def __init__(self, key_vault_url: str, key_name: str):
        self.secret_client = SecretClient(
            vault_url=key_vault_url,
            credential=DefaultAzureCredential()
        )
        self.encryption_key = self._get_encryption_key(key_name)
        self.cipher = Fernet(self.encryption_key)
    
    def encode(self, payloads: List[Payload]) -> List[Payload]:
        """Encrypt payloads before storing in Temporal"""
        encrypted = []
        for payload in payloads:
            encrypted_data = self.cipher.encrypt(payload.data)
            encrypted.append(Payload(
                data=encrypted_data,
                metadata={
                    "encoding": "customer-encrypted/v1",
                    "key_id": self.key_name,
                    "algorithm": "AES-256-GCM"
                }
            ))
        return encrypted
    
    def decode(self, payloads: List[Payload]) -> List[Payload]:
        """Decrypt payloads from Temporal"""
        decrypted = []
        for payload in payloads:
            if payload.metadata.get("encoding") == "customer-encrypted/v1":
                decrypted_data = self.cipher.decrypt(payload.data)
                decrypted.append(Payload(data=decrypted_data))
            else:
                decrypted.append(payload)  # Unencrypted (backward compat)
        return decrypted
```

#### Phase 2: Codec Server (Server-Side Decryption)

**Why Codec Server?**
- Temporal server cannot decrypt (doesn't have keys)
- Codec Server runs in customer's K8s cluster with key access
- Isolated security boundary

**Deployment**: Separate Kubernetes deployment

**Helm Chart**: `infra/helm/codec-server/`

**Configuration**:
```yaml
# values.yaml
codecServer:
  image: engram/codec-server:latest
  replicas: 2
  resources:
    cpu: 0.5
    memory: 512Mi
  env:
    - name: KEY_VAULT_URL
      valueFrom:
        secretKeyRef:
          name: customer-kms-secret
          key: vault-url
    - name: KEY_NAME
      valueFrom:
        secretKeyRef:
          name: customer-kms-secret
          key: key-name
  serviceAccount:
    # Uses customer's managed identity for KMS access
    annotations:
      azure.workload.identity/client-id: ${CUSTOMER_MANAGED_IDENTITY_ID}
```

**Temporal Client Configuration**:
```python
# backend/workflows/client.py
from temporalio.client import Client
from backend.workflows.codec.encryption_codec import CustomerManagedKeyCodec

async def get_temporal_client() -> Client:
    codec = CustomerManagedKeyCodec(
        key_vault_url=settings.customer_key_vault_url,
        key_name=settings.customer_encryption_key_name
    )
    
    return await Client.connect(
        target_host=settings.temporal_host,
        namespace=settings.temporal_namespace,
        data_converter=DataConverter(
            payload_codecs=[codec],
            # Codec Server URL for server-side operations
            codec_server_url=settings.codec_server_url
        )
    )
```

#### Phase 3: Key Rotation Strategy

**NIST AI RMF Requirement**: Regular key rotation

**Implementation**:
1. **Dual-Key Support**: Maintain current + previous key during rotation
2. **Gradual Migration**: Re-encrypt workflows with new key over time
3. **Key Versioning**: Track key versions in payload metadata
4. **Automated Rotation**: Scheduled rotation (e.g., quarterly)

**Key Rotation Workflow**:
```python
@workflow.defn
class EncryptionKeyRotationWorkflow:
    """Rotates encryption keys for all active workflows"""
    
    @workflow.run
    async def run(self, new_key_id: str):
        # 1. Deploy new key to Codec Server
        # 2. Update Data Converter to support both keys
        # 3. Gradually re-encrypt workflows
        # 4. Deprecate old key after grace period
        pass
```

---

## 4. Kubernetes Deployment with Helm Charts

### Current State (Staging POC)

**Current**: Temporal deployed in Azure Container Apps (ACA)
- `temporal-server` Container App
- `temporal-ui` Container App
- PostgreSQL backend

**Limitation**: ACA doesn't support advanced K8s features needed for enterprise:
- Custom RBAC integration
- Pod security policies
- Network policies
- Service mesh integration

### Target State (Customer Environments)

**Deployment**: Temporal OSS via [Helm Charts](https://github.com/temporalio/helm-charts)

**Architecture**:
```
Kubernetes Cluster (Customer's)
├── Temporal Namespace
│   ├── Temporal Server (StatefulSet)
│   │   ├── Frontend (3 replicas)
│   │   ├── History (3 replicas)
│   │   ├── Matching (3 replicas)
│   │   └── Worker (2 replicas)
│   ├── Temporal Admin Tools
│   ├── Temporal Web UI
│   └── Codec Server (Separate deployment)
├── PostgreSQL (Customer's managed database)
└── Monitoring (Prometheus/Grafana)
```

### Helm Chart Customization

**Base Chart**: `temporalio/temporal` from [helm-charts repo](https://github.com/temporalio/helm-charts)

**Custom Values**: `infra/helm/temporal/values-production.yaml`

**Key Configuration**:
```yaml
# History shard count (IMMUTABLE - set correctly)
server:
  config:
    numHistoryShards: 64
    persistence:
      default:
        historyShardCount: 64

# High availability
server:
  replicaCount:
    frontend: 3
    history: 3
    matching: 3
    worker: 2

# Resource sizing
server:
  resources:
    frontend:
      cpu: 1
      memory: 2Gi
    history:
      cpu: 2
      memory: 4Gi  # History service is memory-intensive

# PostgreSQL connection (customer's database)
server:
  config:
    persistence:
      default:
        sql:
          pluginName: "postgres12"
          connectAddr: "${CUSTOMER_POSTGRES_HOST}:5432"
          connectProtocol: "tcp"
          databaseName: "temporal"
          maxConns: 20
          tls:
            enabled: true
            serverName: "${CUSTOMER_POSTGRES_HOST}"

# Custom RBAC (customer's SSO)
server:
  config:
    publicClient:
      enableGlobalNamespace: false
    authorization:
      authorizer:
        plugin: "authorization-plugin"  # Custom plugin
      claimMapper:
        plugin: "claim-mapper-plugin"   # Maps SSO claims to Temporal roles

# Data Converter + Codec Server
server:
  config:
    dataConverter:
      codecServer:
        endpoint: "http://codec-server:8080"
```

### Deployment Process

**Step 1: Pre-Deployment Assessment**
```bash
# Run shard calculator
python tools/shard-calculator.py \
  --peak-throughput 1000 \
  --growth-factor 2.0 \
  --output shard-recommendation.yaml
```

**Step 2: Generate Custom Values**
```bash
# Merge base + customer-specific config
helm template temporal temporalio/temporal \
  -f values-base.yaml \
  -f values-production.yaml \
  -f customer-overrides.yaml \
  > temporal-manifests.yaml
```

**Step 3: Deploy**
```bash
helm install temporal temporalio/temporal \
  -f values-production.yaml \
  --namespace temporal \
  --create-namespace \
  --wait
```

**Step 4: Verify**
```bash
# Check shard count (cannot be changed after this)
kubectl exec -n temporal temporal-frontend-0 -- \
  tctl admin cluster get-settings | grep numHistoryShards

# Verify encryption
kubectl logs -n temporal codec-server-0 | grep "encryption enabled"
```

---

## 5. NIST AI RMF Compliance Integration

### Framework Mapping

| NIST AI RMF Function | Temporal Implementation | Engram Controls |
|----------------------|-------------------------|-----------------|
| **Govern** | Temporal namespace policies | Customer-defined governance |
| **Map** | Workflow type classification | Sensitivity tagging in metadata |
| **Measure** | Temporal metrics + Evidence Telemetry | Cost, performance, security metrics |
| **Manage** | Workflow signals, human-in-the-loop | Approval workflows, incident response |

### Data Encryption Controls (NIST AI RMF)

**Control ID**: AI-SEC-01 (Data Encryption)

**Implementation**:
1. ✅ **Encryption at Rest**: All workflow history encrypted via Data Converter
2. ✅ **Encryption in Transit**: TLS 1.3 for all Temporal communications
3. ✅ **Key Management**: Customer-managed keys via Codec Server
4. ✅ **Key Rotation**: Automated quarterly rotation
5. ✅ **Access Control**: RBAC + SSO integration

**Evidence**:
- Codec Server deployment manifest
- Key rotation workflow logs
- Encryption metadata in workflow payloads
- Audit logs of key access

### Security Assessment Preparation

**Documentation Required**:
1. **Architecture Diagram**: Show encryption flow (Data Converter → Temporal → Codec Server)
2. **Key Management**: Customer KMS integration details
3. **Access Controls**: RBAC, SSO, audit logging
4. **Compliance Mapping**: NIST AI RMF controls → Engram implementation

**Testing Requirements**:
1. **Encryption Verification**: Verify payloads are encrypted in Temporal storage
2. **Key Rotation Test**: Simulate key rotation without workflow disruption
3. **Access Control Test**: Verify RBAC prevents unauthorized access
4. **Audit Logging Test**: Verify all workflow operations are logged

---

## 6. Operational Responsibilities

### Zimax Networks LC Support Model

**For Customer Environments (dev/test/UAT/prod)**:

| Responsibility | Zimax Networks LC | Customer |
|----------------|------------------|----------|
| Temporal deployment | ✅ Helm chart deployment | Infrastructure provisioning |
| History shard sizing | ✅ Assessment & recommendation | Approval |
| Codec Server deployment | ✅ Implementation | Key management |
| Monitoring & alerting | ✅ Setup & maintenance | Alert response |
| Updates & patches | ✅ Planning & execution | Maintenance windows |
| Troubleshooting | ✅ 24/7 support | Issue reporting |
| Compliance documentation | ✅ Preparation | Audit participation |

**Dedicated Resources Required**:
- **Temporal SME**: Deep expertise in OSS deployment
- **K8s Engineer**: Helm charts, deployment automation
- **Security Engineer**: Encryption, compliance, NIST AI RMF
- **SRE**: Monitoring, alerting, incident response

---

## 7. Implementation Roadmap

### Phase 1: Foundation (Months 1-2)
- [ ] Research and document history shard sizing methodology
- [ ] Build shard calculator tool
- [ ] Create Helm chart customizations
- [ ] Design Codec Server architecture

### Phase 2: Encryption Implementation (Months 2-3)
- [ ] Implement Data Converter with customer KMS integration
- [ ] Build Codec Server (separate K8s deployment)
- [ ] Create key rotation workflow
- [ ] Test encryption end-to-end

### Phase 3: Helm Chart Deployment (Months 3-4)
- [ ] Customize Temporal Helm chart for enterprise
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
- [ ] Validate shard count sizing
- [ ] Test encryption with customer keys
- [ ] Gradual rollout to test/UAT/prod

---

## 8. Risk Mitigation

### Risk: History Shard Under-Provisioning

**Mitigation**:
- Conservative sizing (2x safety factor)
- Monitoring with early warning alerts
- Migration plan documented upfront

### Risk: Encryption Key Compromise

**Mitigation**:
- Key rotation workflow
- Dual-key support during rotation
- Audit logging of all key access
- Isolated Codec Server (separate security boundary)

### Risk: Operational Complexity

**Mitigation**:
- Comprehensive documentation
- Automated deployment (Helm charts)
- Dedicated support team
- Training and runbooks

---

## 9. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| History shard utilization | < 70% | Prometheus metrics |
| Encryption coverage | 100% of sensitive workflows | Audit logs |
| Key rotation success rate | 100% | Rotation workflow logs |
| Deployment time | < 2 hours | Deployment automation |
| Support response time | < 1 hour (P1) | Incident tracking |

---

## 10. Next Steps

1. **Approve this strategy** for customer environment deployment
2. **Allocate resources** for Temporal SME, K8s engineer, security engineer
3. **Begin Phase 1** implementation (shard calculator, Helm chart research)
4. **Engage with customer** security team for KMS integration requirements
5. **Schedule security assessment** preparation timeline

---

## References

- [Temporal Helm Charts](https://github.com/temporalio/helm-charts)
- [Temporal Data Converter Documentation](https://docs.temporal.io/concepts/what-is-a-data-converter)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
- [Temporal History Shard Configuration](https://docs.temporal.io/server/production-deployment-guide)

