---
layout: default
title: Unstructured Enterprise Deployment Strategy
---

# Unstructured Enterprise Deployment Strategy for Engram Platform

## Executive Summary

This document outlines Zimax Networks LC's strategy for deploying Unstructured in customer environments (dev/test/UAT/prod). Unstructured is central to Engram's success as the ETL layer, providing document partitioning and chunking for ingestion into Zep memory. This plan addresses enterprise requirements including partitioning strategy selection, chunking parameter configuration, customer-managed key encryption, connector management, and NIST AI RMF compliance.

**Key Decision**: Unstructured OSS (Python library) integrated into Engram API for customer environments to enable:
- Full control over partitioning and chunking strategies
- Custom configuration per document type
- Data residency in customer-controlled infrastructure
- Cost optimization through right-sizing (vs. Platform consumption-based pricing)
- Integration with customer's existing document processing workflows

---

## 1. Unstructured OSS vs Unstructured Platform: Enterprise Comparison

### Feature Comparison Matrix

| Feature | Unstructured OSS (Python Library) | Unstructured Platform (Managed) | Engram Requirement |
|---------|----------------------------------|--------------------------------|-------------------|
| **Deployment** | Python library integrated into application | Managed service (Dedicated Instance or In-VPC) | ✅ Required - Integrated into Engram API |
| **Partitioning Control** | Full control over strategies (fast, hi_res, auto) | Managed strategies (Basic, Advanced, Platinum) | ✅ Required - Custom strategy per document type |
| **Chunking Control** | Full control over chunking parameters | Managed chunking with customization | ✅ Required - Fine-tuned chunking for RAG |
| **Data Residency** | Customer-controlled (runs in customer infrastructure) | In-VPC option available | ✅ Required - Customer data residency |
| **Encryption Keys** | Customer-managed (application-level) | Platform-managed or In-VPC | ✅ **CRITICAL** - Customer-managed keys required |
| **Connector Management** | Custom implementation per connector | 50+ pre-built connectors | ✅ Required - Custom connector integration |
| **Cost Model** | Infrastructure costs only | Consumption-based pricing | ✅ Required - Predictable costs |
| **Model Selection** | Full control (BYOM) | Managed models or BYOM | ✅ Required - Customer LLM accounts |
| **Multi-Tenancy** | Custom implementation | Built-in workspace isolation | ✅ Required - Customer-defined isolation |
| **On-Call Support** | Zimax Networks LC team | Unstructured support team | ✅ Zimax Networks LC provides support |
| **Partitioning Strategy** | Configurable per request | Pre-configured tiers | ✅ **CRITICAL** - Strategy selection affects quality |
| **Chunking Parameters** | Full control (max_characters, overlap, etc.) | Managed with customization | ✅ Required - RAG-optimized chunking |

### Decision Rationale for OSS

**Why Unstructured OSS for Customer Environments:**

1. **Partitioning Strategy Control**: Engram requires fine-grained control over partitioning strategies (fast vs. hi_res) based on document type and use case. OSS allows per-document strategy selection.

2. **Chunking Optimization**: RAG quality depends heavily on chunking parameters. OSS provides full control over `max_characters`, `new_after_n_chars`, `combine_text_under_n_chars`, enabling optimization for customer-specific use cases.

3. **Cost Predictability**: For enterprise customers with predictable document volumes, OSS integrated into Engram API provides cost predictability vs. Platform consumption-based pricing.

4. **Data Residency**: Customer documents must remain in customer-controlled infrastructure. OSS runs entirely within customer's application, ensuring no data leaves customer environment.

5. **Custom Connector Integration**: Customers may have proprietary document sources. OSS allows custom connector implementation without Platform dependency.

6. **Model Selection**: Customers require BYOM (Bring Your Own Model) for OCR/VLM capabilities. OSS allows direct integration with customer's Azure OpenAI or other LLM accounts.

**Staging POC Exception**: Current library-based integration is acceptable for testing and production. Platform may be considered for specific use cases requiring managed connectors.

---

## 2. Partitioning Strategy Configuration: Critical Quality vs. Performance Trade-offs

### The Challenge

Unstructured's partitioning strategy selection is a **critical decision** that affects:
- **Document Quality**: hi_res provides better extraction but is slower
- **Processing Speed**: fast strategy is quick but may miss complex layouts
- **Cost**: hi_res requires more compute resources (OCR, VLM)
- **Accuracy**: Strategy choice directly impacts downstream RAG quality

Unlike Temporal's immutable history shard count or Zep's vector dimensions, partitioning strategy can be changed per document, but **strategy selection must be standardized** across document types for consistency.

### Partitioning Strategy Selection Matrix

| Strategy | Use Case | Processing Time | Quality | Cost | OCR/VLM Required |
|----------|----------|----------------|---------|------|------------------|
| **fast** | Simple text documents, native PDFs | Fast (seconds) | Good | Low | No |
| **hi_res** | Complex layouts, scanned PDFs, images | Slow (minutes) | Excellent | High | Yes (OCR) |
| **auto** | Mixed document types | Variable | Good-Excellent | Variable | Conditional |
| **ocr_only** | Scanned documents only | Medium | Good | Medium | Yes (OCR only) |

### Engram Platform Strategy Selection

**Standard Strategy Mapping**:

| Document Type | Recommended Strategy | Rationale |
|---------------|---------------------|-----------|
| **Native PDFs** | `fast` | Text already extractable, no OCR needed |
| **Scanned PDFs** | `hi_res` | Requires OCR for text extraction |
| **Images (PNG, JPG)** | `hi_res` | Requires OCR/VLM for text extraction |
| **Word Documents** | `fast` | Native text extraction sufficient |
| **Excel/CSV** | `fast` | Structured data, no OCR needed |
| **Handwritten/Complex** | `hi_res` | Requires VLM for accurate extraction |

**Configuration**:
```python
# backend/etl/processor.py
def select_partitioning_strategy(
    filename: str,
    content_type: str,
    file_content: bytes
) -> str:
    """
    Select partitioning strategy based on document characteristics.
    
    Returns: 'fast', 'hi_res', 'auto', or 'ocr_only'
    """
    # Detect document type
    if content_type == "application/pdf":
        # Check if PDF is scanned (requires OCR)
        if is_scanned_pdf(file_content):
            return "hi_res"
        else:
            return "fast"
    elif content_type.startswith("image/"):
        return "hi_res"  # Images require OCR
    elif content_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        return "fast"  # Native Word docs
    else:
        return "auto"  # Default for unknown types
```

### Management Strategy

#### 1. Pre-Deployment Assessment

**Document Type Analysis Tool** (to be built):
```python
# tools/document-analyzer.py
def analyze_document_requirements(
    sample_documents: List[dict],
    quality_requirements: dict
) -> dict:
    """
    Analyze document types and recommend partitioning strategies.
    
    Returns: Strategy mapping and resource requirements
    """
    strategy_map = {}
    for doc in sample_documents:
        doc_type = detect_document_type(doc)
        strategy = recommend_strategy(doc_type, quality_requirements)
        strategy_map[doc["filename"]] = strategy
    
    return {
        "strategy_mapping": strategy_map,
        "estimated_processing_time": calculate_processing_time(sample_documents, strategy_map),
        "resource_requirements": calculate_resources(strategy_map)
    }
```

#### 2. Configuration Management

**Environment-Specific Configuration**:
```yaml
# backend/config/etl-config.yaml
partitioning:
  default_strategy: "fast"
  strategy_mapping:
    "application/pdf": "auto"  # Auto-detect scanned vs. native
    "image/png": "hi_res"
    "image/jpeg": "hi_res"
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "fast"
  
  hi_res:
    ocr_languages: ["eng"]  # Customer-specific languages
    model: "azure-openai"  # Customer's BYOM
    endpoint: "${CUSTOMER_OPENAI_ENDPOINT}"
```

#### 3. Monitoring and Alerting

**Metrics to Track**:
- `unstructured_partitioning_strategy_distribution` - Track strategy usage
- `unstructured_processing_time_p95` - Alert if > threshold
- `unstructured_quality_score` - Monitor extraction quality
- `unstructured_ocr_failure_rate` - Alert if OCR failures increase

**Alert Thresholds**:
- **Warning**: Processing time p95 > 60 seconds
- **Critical**: OCR failure rate > 5%
- **Warning**: Quality score < 0.85 (if measured)

---

## 3. Chunking Parameter Configuration: RAG Quality Optimization

### The Challenge

Chunking parameters directly impact RAG retrieval quality:
- **Too Large**: Chunks contain multiple topics, reducing retrieval precision
- **Too Small**: Context is fragmented, reducing answer quality
- **No Overlap**: Context boundaries may split related content
- **Poor Boundaries**: Chunks may split sentences or paragraphs

**Chunking parameters are configurable per request**, but **standardization is critical** for consistent RAG performance.

### Chunking Parameter Selection

**Engram Standard Configuration**:
```python
# backend/etl/processor.py
CHUNKING_CONFIG = {
    "max_characters": 1000,  # Maximum chunk size
    "new_after_n_chars": 1500,  # Start new chunk after this many chars
    "combine_text_under_n_chars": 500,  # Combine small chunks
    "overlap": 200,  # Character overlap between chunks
    "chunking_strategy": "by_title"  # Semantic chunking by section
}
```

**Rationale**:
- **max_characters: 1000**: Optimal for most LLM context windows, balances detail vs. context
- **new_after_n_chars: 1500**: Prevents chunks from becoming too large
- **combine_text_under_n_chars: 500**: Avoids overly small chunks that lack context
- **overlap: 200**: Ensures context continuity across chunk boundaries
- **chunking_strategy: by_title**: Preserves document structure (sections, headings)

### Chunking Strategy Comparison

| Strategy | Use Case | Pros | Cons |
|----------|----------|------|------|
| **by_title** | Documents with clear structure | Preserves semantic boundaries | May not work for unstructured docs |
| **by_page** | Page-based documents | Simple, predictable | May split related content |
| **fixed_size** | Uniform chunking needed | Consistent chunk sizes | May split sentences/paragraphs |
| **semantic** | Maximum semantic coherence | Best for RAG quality | More compute-intensive |

**Engram Recommendation**: **by_title** for most documents, with fallback to **semantic** for unstructured content.

### Management Strategy

#### 1. Chunking Quality Testing

**Golden Thread Integration**: Use Golden Thread validation to measure chunking quality impact on RAG.

**Metrics**:
- Retrieval hit rate (chunks retrieved vs. expected)
- Answer quality (grounded in retrieved chunks)
- Chunk boundary accuracy (no split sentences/paragraphs)

#### 2. Configuration Tuning

**Per-Document-Type Tuning**:
```python
# Tune chunking per document type
CHUNKING_CONFIG_BY_TYPE = {
    "policy_documents": {
        "max_characters": 1200,  # Policies need more context
        "chunking_strategy": "by_title"
    },
    "meeting_notes": {
        "max_characters": 800,  # Notes are more concise
        "chunking_strategy": "semantic"
    },
    "technical_docs": {
        "max_characters": 1000,
        "chunking_strategy": "by_title"
    }
}
```

---

## 4. Data Encryption: Customer-Managed Keys for Document Processing

### NIST AI RMF Alignment

Per [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework), data encryption requirements:

**Govern Function**:
- Establish encryption policies for document processing (PII, PHI, business secrets)
- Define key management responsibilities

**Map Function**:
- Identify sensitive data in documents (PII in PDFs, PHI in medical records, business secrets)
- Map encryption requirements to document types

**Measure Function**:
- Verify encryption at rest and in transit
- Audit key rotation and access

**Manage Function**:
- Implement customer-managed key rotation
- Monitor encryption compliance

### Unstructured Encryption Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Engram Platform                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Document Upload (Encrypted in Transit)                 │
│         │                                                │
│         ▼                                                │
│  ┌──────────────────┐                                   │
│  │ Engram API       │ ← TLS 1.3 encryption              │
│  │ (FastAPI)        │   - Document received encrypted   │
│  └──────────────────┘                                   │
│         │                                                │
│         ▼                                                │
│  ┌──────────────────┐                                   │
│  │ Document Storage │ ← Temporary storage (encrypted)   │
│  │ (Azure Blob)     │   - Customer-managed keys        │
│  └──────────────────┘   - TDE enabled                  │
│         │                                                │
│         ▼                                                │
│  ┌──────────────────┐                                   │
│  │ Unstructured OSS │ ← Processing (in-memory)          │
│  │ (Python Library) │   - No persistent storage         │
│  └──────────────────┘   - Runs in customer K8s          │
│         │                                                │
│         ▼                                                │
│  ┌──────────────────┐                                   │
│  │ Chunk Storage    │ ← Encrypted chunks                │
│  │ (Zep/PostgreSQL) │   - PostgreSQL TDE                │
│  └──────────────────┘   - Customer-managed keys        │
│         │                                                │
│         ▼                                                │
│  ┌──────────────────┐                                   │
│  │ Azure Key Vault  │ ← Customer-managed encryption keys│
│  │ (Customer KMS)   │   - Full control over keys        │
│  └──────────────────┘   - Key rotation capability       │
└─────────────────────────────────────────────────────────┘
```

### Implementation Plan

#### Phase 1: Document Storage Encryption

**Azure Blob Storage TDE**:
- Built-in encryption using Azure Key Vault
- Customer-managed keys (CMK) supported
- Zero application changes required

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
      }
    }
  }
}
```

#### Phase 2: In-Memory Processing Security

**Processing Security**:
- Documents processed in-memory (no persistent storage during processing)
- Temporary files encrypted if written to disk
- Process isolation in Kubernetes pods

**Configuration**:
```yaml
# Kubernetes pod security
securityContext:
  runAsNonRoot: true
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
```

#### Phase 3: Chunk Encryption

**PostgreSQL TDE**: Chunks stored in Zep/PostgreSQL are encrypted via PostgreSQL TDE (covered in Zep deployment strategy).

---

## 5. Kubernetes Deployment Strategy

### Current State (Staging POC)

**Current**: Unstructured OSS integrated into Engram API Container App
- Python library (`unstructured[all-docs]`) installed in API container
- Processing happens synchronously in API request handler
- No separate service deployment

**Limitation**: Synchronous processing blocks API requests for large documents.

### Target State (Customer Environments)

**Deployment**: Unstructured OSS integrated into Engram API with optional worker pool

**Architecture**:
```
Kubernetes Cluster (Customer's)
├── Engram API Namespace
│   ├── API Server (Deployment)
│   │   ├── FastAPI application
│   │   ├── Unstructured OSS library
│   │   └── Document processing (synchronous for small docs)
│   ├── ETL Worker Pool (Optional, Deployment)
│   │   ├── Background document processing
│   │   ├── Unstructured OSS library
│   │   └── Async processing for large documents
│   └── Monitoring (Prometheus exporters)
├── Azure Blob Storage (Customer's managed storage)
│   └── Document storage (encrypted, TDE)
└── PostgreSQL (Customer's managed database)
    └── Chunk storage (via Zep, encrypted)
```

### Deployment Configuration

**Helm Chart Values**: `infra/helm/engram-api/values-production.yaml`

**Key Configuration**:
```yaml
# Unstructured OSS configuration
unstructured:
  enabled: true
  library_version: "0.12.0"
  extras: ["all-docs"]  # Install all document type support
  
  # Partitioning strategy configuration
  partitioning:
    default_strategy: "fast"
    hi_res_enabled: true
    ocr_model: "azure-openai"  # Customer's BYOM
    ocr_endpoint: "${CUSTOMER_OPENAI_ENDPOINT}"
  
  # Chunking configuration
  chunking:
    max_characters: 1000
    new_after_n_chars: 1500
    combine_text_under_n_chars: 500
    overlap: 200
    strategy: "by_title"
  
  # Resource requirements
  resources:
    requests:
      cpu: "500m"
      memory: "2Gi"
    limits:
      cpu: "2"
      memory: "4Gi"  # hi_res processing is memory-intensive

# Optional: ETL Worker Pool for async processing
etl_workers:
  enabled: true
  replicas: 2
  resources:
    requests:
      cpu: "1"
      memory: "4Gi"
    limits:
      cpu: "4"
      memory: "8Gi"
```

### Deployment Process

**Step 1: Install Unstructured OSS**
```bash
# In Dockerfile or requirements.txt
pip install unstructured[all-docs]>=0.12.0
```

**Step 2: Configure Partitioning Strategy**
```bash
# Set environment variables
export UNSTRUCTURED_DEFAULT_STRATEGY=fast
export UNSTRUCTURED_HI_RES_ENABLED=true
export UNSTRUCTURED_OCR_MODEL=azure-openai
export UNSTRUCTURED_OCR_ENDPOINT=${CUSTOMER_OPENAI_ENDPOINT}
```

**Step 3: Deploy Engram API**
```bash
helm install engram-api ./infra/helm/engram-api \
  -f values-production.yaml \
  --namespace engram \
  --create-namespace \
  --wait
```

**Step 4: Verify**
```bash
# Test document processing
curl -X POST https://api.engram.example.com/api/v1/etl/ingest \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "file=@test-document.pdf"

# Check processing metrics
kubectl logs -n engram engram-api-0 | grep "Partitioning file"
```

---

## 6. NIST AI RMF Compliance Integration

### Framework Mapping

| NIST AI RMF Function | Unstructured Implementation | Engram Controls |
|----------------------|----------------------------|-----------------|
| **Govern** | Document processing policies, data classification | Customer-defined governance |
| **Map** | Document type classification, sensitivity tagging | PII/PHI detection and handling |
| **Measure** | Processing quality metrics, extraction accuracy | Golden Thread validation |
| **Manage** | Document retention, GDPR compliance, key rotation | Data lifecycle management |

### Data Encryption Controls (NIST AI RMF)

**Control ID**: AI-SEC-01 (Data Encryption)

**Implementation**:
1. ✅ **Encryption at Rest**: All documents encrypted via Azure Blob Storage TDE
2. ✅ **Encryption in Transit**: TLS 1.3 for all API communications
3. ✅ **Key Management**: Customer-managed keys via Azure Key Vault
4. ✅ **Key Rotation**: Automated quarterly rotation
5. ✅ **Processing Security**: In-memory processing, no persistent storage

**Evidence**:
- Azure Blob Storage TDE configuration manifest
- Key rotation workflow logs
- Encryption metadata in document storage
- Audit logs of key access

### Security Assessment Preparation

**Documentation Required**:
1. **Architecture Diagram**: Show encryption flow (Upload → Blob Storage TDE → Processing → Zep/PostgreSQL TDE)
2. **Key Management**: Customer KMS integration details
3. **Access Controls**: RBAC, SSO, audit logging
4. **Compliance Mapping**: NIST AI RMF controls → Engram implementation

**Testing Requirements**:
1. **Encryption Verification**: Verify documents are encrypted in Blob Storage
2. **Key Rotation Test**: Simulate key rotation without data loss
3. **Access Control Test**: Verify RBAC prevents unauthorized document access
4. **Audit Logging Test**: Verify all document operations are logged

---

## 7. Operational Responsibilities

### Zimax Networks LC Support Model

**For Customer Environments (dev/test/UAT/prod)**:

| Responsibility | Zimax Networks LC | Customer |
|----------------|------------------|----------|
| Unstructured OSS integration | ✅ Library integration & configuration | Application deployment |
| Partitioning strategy tuning | ✅ Configuration & optimization | Document type requirements |
| Chunking parameter optimization | ✅ Tuning & validation | RAG quality requirements |
| Document storage encryption | ✅ Blob Storage TDE setup | Key management |
| Monitoring & alerting | ✅ Setup & maintenance | Alert response |
| Updates & patches | ✅ Planning & execution | Maintenance windows |
| Troubleshooting | ✅ 24/7 support | Issue reporting |
| Compliance documentation | ✅ Preparation | Audit participation |

**Dedicated Resources Required**:
- **ETL Engineer**: Unstructured OSS expertise, partitioning/chunking optimization
- **ML Engineer**: OCR/VLM model integration, quality optimization
- **K8s Engineer**: Deployment automation, resource optimization
- **Security Engineer**: Encryption, compliance, NIST AI RMF
- **SRE**: Monitoring, alerting, incident response

---

## 8. Implementation Roadmap

### Phase 1: Foundation (Months 1-2)
- [ ] Research and document partitioning strategy selection methodology
- [ ] Build document type analyzer tool
- [ ] Create chunking parameter optimization guide
- [ ] Design encryption architecture

### Phase 2: Encryption Implementation (Months 2-3)
- [ ] Configure Azure Blob Storage TDE with customer-managed keys
- [ ] Implement in-memory processing security
- [ ] Create key rotation workflow
- [ ] Test encryption end-to-end

### Phase 3: Configuration Optimization (Months 3-4)
- [ ] Tune partitioning strategies per document type
- [ ] Optimize chunking parameters for RAG quality
- [ ] Integrate with Golden Thread validation
- [ ] Document configuration procedures

### Phase 4: Compliance & Documentation (Months 4-5)
- [ ] Map NIST AI RMF controls to implementation
- [ ] Create security assessment documentation
- [ ] Prepare audit evidence
- [ ] Train support team

### Phase 5: Production Deployment (Months 5-6)
- [ ] Deploy to customer dev environment
- [ ] Validate partitioning/chunking quality
- [ ] Test encryption with customer keys
- [ ] Gradual rollout to test/UAT/prod

---

## 9. Risk Mitigation

### Risk: Poor Partitioning Strategy Selection

**Mitigation**:
- Document type analysis tool
- Standardized strategy mapping
- Quality monitoring and alerting
- Fallback strategies for unknown types

### Risk: Suboptimal Chunking Parameters

**Mitigation**:
- Golden Thread validation integration
- Per-document-type tuning
- RAG quality metrics
- Continuous optimization based on retrieval performance

### Risk: Encryption Key Compromise

**Mitigation**:
- Key rotation workflow
- Dual-key support during rotation
- Audit logging of all key access
- Azure Blob Storage TDE with customer-managed keys

### Risk: Processing Performance Issues

**Mitigation**:
- Async worker pool for large documents
- Resource limits and monitoring
- Strategy selection based on document complexity
- Performance testing in UAT

---

## 10. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Document processing time p95 | < 30s (fast), < 5m (hi_res) | Application metrics |
| Partitioning quality score | > 0.90 | Golden Thread validation |
| Chunking RAG hit rate | > 90% | Retrieval quality metrics |
| Encryption coverage | 100% of documents | Audit logs |
| Key rotation success rate | 100% | Rotation workflow logs |
| Processing error rate | < 1% | Application metrics |
| Support response time | < 1 hour (P1) | Incident tracking |

---

## 11. Next Steps

1. **Approve this strategy** for customer environment deployment
2. **Allocate resources** for ETL engineer, ML engineer, K8s engineer, security engineer
3. **Begin Phase 1** implementation (document analyzer, partitioning strategy guide)
4. **Engage with customer** document team for document type requirements
5. **Schedule security assessment** preparation timeline

---

## References

- [Unstructured Documentation](https://docs.unstructured.io/)
- [Unstructured Python Library](https://github.com/Unstructured-IO/unstructured)
- [Azure Blob Storage Encryption](https://learn.microsoft.com/azure/storage/common/storage-service-encryption)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)

