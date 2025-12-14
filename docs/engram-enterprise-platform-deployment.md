---
layout: default
title: Engram Enterprise Platform Deployment Strategy
---

# Engram Enterprise Platform Deployment Strategy

## Executive Summary

This document provides a **unified enterprise deployment strategy** for the complete Engram platform, integrating all core components: **Temporal** (Durable Spine), **Zep** (Memory Layer), **Unstructured** (ETL Layer), **PostgreSQL/Blob Storage** (Data Layer), and **Navigation UI** (Integration Layer). This master plan addresses enterprise requirements for deploying the full Engram stack in customer environments (dev/test/UAT/prod), including component integration, data flows, unified encryption, NIST AI RMF compliance, and operational responsibilities.

**Platform Overview**: Engram is a **Cognition-as-a-Service** platform that orchestrates AI agents through durable workflows, maintains provenance-first memory, processes documents with layout-aware fidelity, and provides a unified enterprise interface. All components are deployed in customer-controlled infrastructure with customer-managed encryption keys.

**Key Decision**: Self-hosted OSS components (Temporal OSS, Zep OSS, Unstructured OSS) integrated with customer-managed infrastructure (PostgreSQL, Blob Storage) and a React-based Navigation UI, all deployed in customer Kubernetes environments to enable:
- Full control over data encryption with customer-managed keys
- Data residency in customer-controlled infrastructure
- Custom RBAC, SSO, and compliance controls
- Cost optimization through right-sizing
- Unified enterprise interface for all capabilities

---

## 1. Platform Architecture: Component Integration

### Complete Platform Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                    Engram Enterprise Platform                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Navigation UI (React + FastAPI)                    │  │
│  │         Integration Layer                                 │  │
│  │         - TreeNav Component                                │  │
│  │         - Service Layer (api.ts, bau.ts, metrics.ts)      │  │
│  │         - FastAPI Routers (Agents, Chat, Memory, etc.)    │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                         │
│         ┌─────────────┼─────────────┐                           │
│         │             │             │                           │
│         ▼             ▼             ▼                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│  │ Temporal │  │   Zep    │  │Unstructured│                     │
│  │  (OSS)   │  │  (OSS)   │  │   (OSS)   │                     │
│  │          │  │          │  │           │                     │
│  │ Durable  │  │  Memory  │  │    ETL    │                     │
│  │  Spine   │  │  Layer   │  │   Layer   │                     │
│  └────┬─────┘  └────┬─────┘  └─────┬─────┘                     │
│       │             │              │                            │
│       │             │              │                            │
│       └─────────────┼──────────────┘                            │
│                     │                                            │
│                     ▼                                            │
│         ┌──────────────────────┐                                │
│         │   Data Layer          │                                │
│         │                       │                                │
│         │  ┌──────────────┐    │                                │
│         │  │  PostgreSQL  │    │                                │
│         │  │  (pgvector)  │    │                                │
│         │  │  System of   │    │                                │
│         │  │  Recall      │    │                                │
│         │  └──────────────┘    │                                │
│         │                       │                                │
│         │  ┌──────────────┐    │                                │
│         │  │ Blob Storage │    │                                │
│         │  │  System of   │    │                                │
│         │  │  Record      │    │                                │
│         │  └──────────────┘    │                                │
│         └──────────────────────┘                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Role | Key Function | Deployment |
|-----------|------|--------------|------------|
| **Navigation UI** | Integration Layer | Unified interface, API gateway, user flows | Azure Static Web Apps + FastAPI Container |
| **Temporal OSS** | Durable Spine | Workflow orchestration, state management, signals/queries | Kubernetes (customer cluster) |
| **Zep OSS** | Memory Layer | Episodic memory (conversations), semantic memory (Graphiti), vector search | Kubernetes + PostgreSQL |
| **Unstructured OSS** | ETL Layer | Document partitioning, chunking, layout-aware parsing | Integrated in FastAPI Container |
| **PostgreSQL (pgvector)** | System of Recall | Vector embeddings, knowledge graph, episodic memory storage | Azure Database for PostgreSQL Flexible Server |
| **Blob Storage** | System of Record | Raw documents, parsed artifacts, provenance metadata | Azure Blob Storage |

---

## 2. Component Integration Matrix

### How Components Connect

| Integration Point | Source Component | Target Component | Protocol | Purpose |
|-------------------|------------------|------------------|----------|---------|
| **Document Ingestion** | Navigation UI | Unstructured (via FastAPI) | HTTP/REST | Upload documents for processing |
| **Document Processing** | Unstructured | Blob Storage | Azure SDK | Store parsed artifacts |
| **Memory Indexing** | Unstructured | Zep (via FastAPI) | HTTP/REST | Index chunks to semantic memory |
| **Vector Storage** | Zep | PostgreSQL (pgvector) | PostgreSQL Protocol | Store vector embeddings |
| **Workflow Orchestration** | Navigation UI | Temporal | gRPC | Start/monitor workflows |
| **Memory Retrieval** | Temporal Activities | Zep (via FastAPI) | HTTP/REST | Retrieve context for agents |
| **Agent Execution** | Temporal Workflows | Zep Memory | HTTP/REST | Query memory during agent turns |
| **Workflow Status** | Temporal | Navigation UI (via FastAPI) | gRPC → HTTP/REST | Display workflow status |
| **Evidence Collection** | All Components | Navigation UI | HTTP/REST | Telemetry and metrics |
| **Document Retrieval** | Zep Memory | Blob Storage | Azure SDK | Link memory to source documents |

### Data Flow: Document to Agent Response

```
1. User uploads document via Navigation UI
   │
   ▼
2. FastAPI ETL Router receives document
   │
   ▼
3. Unstructured OSS processes document (partitioning + chunking)
   │
   ├──► Chunks → Zep API → PostgreSQL (pgvector) [System of Recall]
   │
   └──► Parsed artifacts → Blob Storage [System of Record]
   │
   ▼
4. User starts conversation via Navigation UI
   │
   ▼
5. FastAPI Chat Router → Temporal Workflow (AgentWorkflow)
   │
   ▼
6. Temporal Activity: search_memory → Zep API
   │
   ▼
7. Zep queries PostgreSQL (pgvector) for relevant chunks
   │
   ▼
8. Temporal Activity: generate_response (with retrieved context)
   │
   ▼
9. Response returned to Navigation UI
   │
   ▼
10. User views workflow execution in Navigation UI
```

---

## 3. Enterprise Deployment Strategy: Unified Approach

### Deployment Architecture

**Customer Kubernetes Cluster**:
- **Temporal OSS**: Deployed via Helm charts, manages workflow execution
- **Zep OSS**: Deployed as Kubernetes service, connects to PostgreSQL
- **FastAPI Container**: Includes Unstructured OSS, serves Navigation UI backend

**Customer Azure Infrastructure**:
- **PostgreSQL Flexible Server**: Zep memory storage with pgvector
- **Blob Storage**: Document storage with lifecycle management
- **Static Web Apps**: Navigation UI frontend
- **Container Apps**: FastAPI backend (scale-to-zero)

**Customer Key Vault**:
- **Unified Encryption Keys**: Single customer-managed key for all components
  - PostgreSQL TDE
  - Blob Storage TDE
  - Temporal Data Converter (Codec Server)
  - Application-level encryption (if needed)

### Deployment Sequence

1. **Phase 1: Data Layer** (PostgreSQL + Blob Storage)
   - Provision PostgreSQL Flexible Server with pgvector
   - Configure Blob Storage with lifecycle policies
   - Set up customer-managed encryption keys

2. **Phase 2: Memory Layer** (Zep OSS)
   - Deploy Zep to Kubernetes
   - Configure PostgreSQL connection
   - Set up Graphiti knowledge graph
   - Test vector search

3. **Phase 3: ETL Layer** (Unstructured OSS)
   - Integrate Unstructured into FastAPI
   - Configure partitioning strategies
   - Test document processing

4. **Phase 4: Durable Spine** (Temporal OSS)
   - Deploy Temporal to Kubernetes
   - Configure history shards (immutable)
   - Set up Data Converter + Codec Server
   - Test workflow execution

5. **Phase 5: Integration Layer** (Navigation UI)
   - Deploy FastAPI backend
   - Deploy React frontend
   - Configure authentication/SSO
   - Test end-to-end flows

---

## 4. Unified Encryption Strategy

### Customer-Managed Keys (CMK) Across All Components

**Single Key Vault Approach**:
- One Azure Key Vault for all encryption keys
- Unified key rotation workflow
- Single audit trail for key access

**Component Encryption**:

| Component | Encryption Method | Key Source | Configuration |
|-----------|------------------|------------|---------------|
| **PostgreSQL** | TDE (Transparent Data Encryption) | Customer Key Vault | Azure PostgreSQL Flexible Server TDE |
| **Blob Storage** | Storage Service Encryption | Customer Key Vault | Blob Storage TDE with CMK |
| **Temporal** | Data Converter + Codec Server | Customer Key Vault | Custom encryption in workflow data |
| **Zep** | Inherits from PostgreSQL | Customer Key Vault | PostgreSQL TDE covers Zep data |
| **Unstructured** | Inherits from Blob Storage | Customer Key Vault | Blob Storage TDE covers documents |

**Key Rotation Strategy**:
1. Quarterly automated rotation
2. Dual-key support during rotation
3. Zero-downtime rotation for all components
4. Unified rotation workflow

---

## 5. NIST AI RMF Compliance: Platform-Level

### Framework Mapping Across Components

| NIST AI RMF Function | Temporal | Zep | Unstructured | PostgreSQL/Blob | Navigation UI | Platform Control |
|---------------------|----------|-----|--------------|----------------|---------------|------------------|
| **Govern** | Workflow policies | Memory retention | Partitioning config | Lifecycle policies | Settings UI | Unified governance |
| **Map** | Workflow metadata | Data classification | Document tagging | Tier classification | Provenance display | End-to-end mapping |
| **Measure** | Workflow metrics | Memory quality | Parse success | Performance metrics | Telemetry dashboard | Unified metrics |
| **Manage** | Workflow controls | Memory management | Chunking optimization | Backup/restore | User flows | Platform management |

### Compliance Evidence

**Data Encryption**:
- ✅ PostgreSQL TDE with customer-managed keys
- ✅ Blob Storage TDE with customer-managed keys
- ✅ Temporal Data Converter encryption
- ✅ Unified key rotation workflow

**Access Control**:
- ✅ RBAC at Navigation UI level
- ✅ Tenant isolation in Zep memory
- ✅ Workflow access control in Temporal
- ✅ Document access control in Blob Storage

**Audit Trail**:
- ✅ Workflow execution logs (Temporal)
- ✅ Memory access logs (Zep)
- ✅ Document processing logs (Unstructured)
- ✅ API access logs (FastAPI)
- ✅ Unified audit dashboard (Navigation UI)

**Provenance**:
- ✅ Document source tracking (Blob Storage)
- ✅ Memory fact provenance (Zep)
- ✅ Workflow trace IDs (Temporal)
- ✅ End-to-end traceability (Navigation UI)

---

## 6. Operational Responsibilities: Full Stack Support

### Zimax Networks LC Support Model

**For Customer Environments (dev/test/UAT/prod)**:

| Responsibility | Zimax Networks LC | Customer |
|----------------|------------------|----------|
| **Platform Deployment** | ✅ Coordinated deployment of all components | Infrastructure approval |
| **Component Integration** | ✅ Integration testing and validation | Integration requirements |
| **Unified Encryption** | ✅ CMK configuration across all components | Key management |
| **Performance Optimization** | ✅ Cross-component optimization | Performance requirements |
| **Monitoring & Alerting** | ✅ Unified monitoring dashboard | Alert response |
| **Backup & Disaster Recovery** | ✅ Coordinated backup strategy | RPO/RTO requirements |
| **Updates & Patches** | ✅ Coordinated update planning | Maintenance windows |
| **Troubleshooting** | ✅ 24/7 support for all components | Issue reporting |
| **Compliance Documentation** | ✅ Platform-level compliance evidence | Audit participation |

**Dedicated Resources Required**:
- **Platform Architect**: Overall architecture and integration
- **Temporal Engineer**: Workflow orchestration expertise
- **Zep/PostgreSQL DBA**: Memory layer optimization
- **ETL Engineer**: Unstructured configuration
- **Frontend/Backend Engineers**: Navigation UI development
- **DevOps Engineer**: Kubernetes deployment and monitoring
- **Security Engineer**: Encryption and compliance
- **SRE**: Monitoring, alerting, incident response

---

## 7. Implementation Roadmap: Coordinated Deployment

### Phase 1: Foundation (Months 1-2)
- [ ] Platform architecture design
- [ ] Component integration planning
- [ ] Unified encryption architecture
- [ ] Customer infrastructure assessment
- [ ] Resource allocation

### Phase 2: Data Layer Deployment (Months 2-3)
- [ ] PostgreSQL Flexible Server provisioning
- [ ] Blob Storage configuration
- [ ] Customer-managed key setup
- [ ] Lifecycle policy configuration
- [ ] Performance baseline testing

### Phase 3: Memory & ETL Layers (Months 3-4)
- [ ] Zep OSS deployment to Kubernetes
- [ ] PostgreSQL connection and testing
- [ ] Unstructured OSS integration
- [ ] Document processing testing
- [ ] Memory indexing validation

### Phase 4: Durable Spine (Months 4-5)
- [ ] Temporal OSS deployment to Kubernetes
- [ ] History shard configuration
- [ ] Data Converter + Codec Server setup
- [ ] Workflow execution testing
- [ ] Integration with Zep memory

### Phase 5: Integration Layer (Months 5-6)
- [ ] FastAPI backend deployment
- [ ] Navigation UI frontend deployment
- [ ] Authentication/SSO integration
- [ ] End-to-end flow testing
- [ ] Performance optimization

### Phase 6: Production Readiness (Months 6-7)
- [ ] Security assessment
- [ ] Compliance documentation
- [ ] Disaster recovery testing
- [ ] Load testing
- [ ] Gradual production rollout

---

## 8. Risk Mitigation: Platform-Level

### Risk: Component Integration Failures

**Mitigation**:
- Comprehensive integration testing
- Service layer abstraction for resilience
- Circuit breakers for component failures
- Graceful degradation strategies

### Risk: Data Consistency Across Components

**Mitigation**:
- Eventual consistency patterns
- Idempotent operations
- Transaction boundaries where possible
- Data validation at integration points

### Risk: Performance Bottlenecks

**Mitigation**:
- Cross-component performance monitoring
- Caching at integration points
- Async processing for long-running tasks
- Right-sizing all components

### Risk: Encryption Key Compromise

**Mitigation**:
- Unified key rotation workflow
- Isolated Key Vault (separate security boundary)
- Audit logging of all key access
- Dual-key support during rotation

### Risk: Deployment Coordination Failures

**Mitigation**:
- Coordinated deployment runbooks
- Dependency mapping
- Rollback procedures for each component
- Staged deployment approach

---

## 9. Success Metrics: Platform-Wide

| Metric | Target | Measurement | Components Involved |
|--------|--------|-------------|---------------------|
| **End-to-End Latency** | < 2s (document → response) | Request tracing | Navigation UI → Temporal → Zep → Response |
| **Document Processing Time** | < 5s (p95) | ETL metrics | Unstructured → Blob Storage → Zep |
| **Memory Retrieval Time** | < 200ms (p95) | Zep metrics | Zep → PostgreSQL (pgvector) |
| **Workflow Execution Success** | > 99.5% | Temporal metrics | Temporal workflow completion |
| **Platform Uptime** | > 99.9% | Unified monitoring | All components |
| **Encryption Coverage** | 100% | Security audit | All data at rest |
| **API Error Rate** | < 1% | FastAPI metrics | Navigation UI backend |
| **User Satisfaction (NPS)** | > 50 | User surveys | Navigation UI |

---

## 10. Component-Specific Deployment Documents

This master document provides the unified platform strategy. For detailed component-specific deployment strategies, refer to:

1. **[Temporal Enterprise Deployment Strategy](temporal-enterprise-deployment.md)**
   - Temporal OSS vs. Temporal Cloud comparison
   - History shard count management
   - Data encryption with customer-managed keys (Codec Server)
   - Kubernetes deployment with Helm charts
   - NIST AI RMF alignment

2. **[Zep Enterprise Deployment Strategy](zep-enterprise-deployment.md)**
   - Zep OSS vs. Zep Cloud comparison
   - PostgreSQL/pgvector configuration and sizing
   - Data encryption with customer-managed keys
   - Graphiti knowledge graph management
   - NIST AI RMF alignment

3. **[Unstructured Enterprise Deployment Strategy](unstructured-enterprise-deployment.md)**
   - Unstructured OSS vs. Unstructured Platform comparison
   - Partitioning/chunking configuration strategy
   - Data encryption with customer-managed keys
   - Kubernetes deployment
   - Connector ecosystem
   - NIST AI RMF alignment

4. **[PostgreSQL & Blob Storage Enterprise Deployment Strategy](postgresql-blob-storage-enterprise-deployment.md)**
   - PostgreSQL Flexible Server vs. alternatives
   - SKU selection and sizing strategy
   - Blob Storage tier selection and lifecycle management
   - Customer-managed key encryption
   - Integration patterns
   - NIST AI RMF alignment

5. **[Navigation UI Enterprise Deployment Strategy](navigation-ui-enterprise-deployment.md)**
   - Frontend-backend integration architecture
   - Navigation patterns and user flows
   - Enterprise deployment considerations
   - Integration with all Engram components
   - Authentication and RBAC
   - NIST AI RMF compliance from UI/UX perspective

---

## 11. Next Steps

1. **Approve this unified platform strategy** for customer environment deployment
2. **Review component-specific documents** for detailed deployment requirements
3. **Allocate resources** for Platform Architect, component engineers, DevOps, Security, SRE
4. **Engage with customer** for infrastructure requirements and IdP integration
5. **Begin Phase 1** implementation (platform architecture, infrastructure assessment)
6. **Schedule security assessment** preparation timeline

---

## References

### Component Documentation
- [Temporal Enterprise Deployment Strategy](temporal-enterprise-deployment.md)
- [Zep Enterprise Deployment Strategy](zep-enterprise-deployment.md)
- [Unstructured Enterprise Deployment Strategy](unstructured-enterprise-deployment.md)
- [PostgreSQL & Blob Storage Enterprise Deployment Strategy](postgresql-blob-storage-enterprise-deployment.md)
- [Navigation UI Enterprise Deployment Strategy](navigation-ui-enterprise-deployment.md)

### External References
- [Temporal Documentation](https://docs.temporal.io/)
- [Zep Documentation](https://docs.getzep.com/)
- [Unstructured Documentation](https://unstructured.io/docs/)
- [Azure Database for PostgreSQL](https://learn.microsoft.com/azure/postgresql/)
- [Azure Blob Storage](https://learn.microsoft.com/azure/storage/blobs/)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)

