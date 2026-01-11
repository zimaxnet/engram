# OpenContextGraph (ctxgraph) — Master System Specification

**Purpose:** Complete technical specification for rebuilding the Engram system as a FedRAMP High deployable on-prem platform.

**Repository:** `github.com/derekbmoore/openContextGraph` (personal, MIT license)  
**Short Name:** ctxgraph

---

## 1. System Overview

### 1.1 Core Mission

**OpenContextGraph (ctxgraph)** is an enterprise AI context orchestration platform that solves the **Memory Wall Problem** — the inability of LLMs to maintain persistent, attributable, scoped memory across interactions.

### 1.2 Unique Differentiators

| Capability | What We Do | What Others Cannot |
|------------|------------|---------------------|
| **Temporal Knowledge Graph** | Memory decays, relationships evolve, context is temporal | Static RAG with no time dimension |
| **4-Layer Security Context** | Identity → Episodic → Semantic → Operational | Flat security with no enterprise boundaries |
| **Tri-Search™** | Keyword + Vector + Graph fusion with RRF | Single-mode search only |
| **Antigravity Router** | Truth-value classification (Class A/B/C) | Generic document loaders |
| **Provenance Tracking** | Every fact links to source + timestamp | Anonymous knowledge bases |
| **Agent Attribution** | All agent actions traceable to invoking user | Black-box agent execution |

---

## 2. Architecture Layers

### 2.1 Brain Layer (LangGraph Agents)

Reasoning and decision-making agents.

| Agent | Role | Capabilities |
|-------|------|--------------|
| **Elena** | Senior System Architect | Architecture analysis, technical guidance |
| **Marcus** | Project Manager | Timelines, risk assessment, project tracking |
| **Sage** | Storyteller | Narrative generation, visual storytelling |

**Implementation:** `backend/agents/`

- `foundry_client.py` — Azure AI model integration
- `router.py` — Agent selection logic
- `elena/`, `marcus/`, `sage/` — Agent-specific logic

### 2.2 Spine Layer (Temporal Workflows)

Durable, fault-tolerant orchestration.

| Workflow | Purpose |
|----------|---------|
| `story_workflow.py` | Multi-step story generation with image creation |
| `ingestion_workflow.py` | Document processing pipeline |
| `memory_enrichment.py` | Context injection workflows |

**Implementation:** `backend/workflows/`

- Temporal Cloud or self-hosted Temporal Server
- Worker: `backend/workflows/worker.py`

### 2.3 CtxGraph Layer (Memory)

Temporal knowledge graph with Zep + Graphiti.

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Episodic Memory** | Zep Sessions | Conversation history per user |
| **Semantic Memory** | Zep Facts + Graphiti | Knowledge graph with entities/relationships |
| **Hybrid Search** | Zep Tri-Search | Keyword + Vector + Graph fusion |

**Implementation:** `backend/memory/client.py`

- ZepMemoryClient with REST API integration
- Tri-Search with Reciprocal Rank Fusion (RRF)

---

## 3. Security Architecture (4-Layer Context Schema)

### 3.1 Layer 1: SecurityContext (Identity)

```
┌─────────────────────────────────────────┐
│ SecurityContext (Layer 1)                │
├─────────────────────────────────────────┤
│ user_id: str     (from Entra ID/OIDC)   │
│ tenant_id: str   (multi-tenant isolation)│
│ roles: [ADMIN, ANALYST, PM, VIEWER]     │
│ scopes: [project:read, project:write]   │
└─────────────────────────────────────────┘
```

**Implementation:** `backend/api/middleware/auth.py`

- EntraIDAuth class with JWT validation
- RBAC enforcement with `require_roles()` decorator
- Multi-tenant isolation via tenant_id filtering

### 3.2 Layer 2: EpisodicContext (Conversation)

```
┌─────────────────────────────────────────┐
│ EpisodicContext (Layer 2)               │
├─────────────────────────────────────────┤
│ conversation_id: str                    │
│ turn_count: int                         │
│ recent_messages: list[Message]          │
│ channel: chat | voice | episode         │
└─────────────────────────────────────────┘
```

### 3.3 Layer 3: SemanticContext (Knowledge)

```
┌─────────────────────────────────────────┐
│ SemanticContext (Layer 3)               │
├─────────────────────────────────────────┤
│ facts: list[Fact]                       │
│ entities: list[Entity]                  │
│ graph_nodes: list[GraphNode]            │
│ relevance_scores: dict                  │
└─────────────────────────────────────────┘
```

### 3.4 Layer 4: OperationalContext (Runtime)

```
┌─────────────────────────────────────────┐
│ OperationalContext (Layer 4)            │
├─────────────────────────────────────────┤
│ current_agent: str                      │
│ tool_calls: list[ToolCall]              │
│ latency_budget_ms: int                  │
│ cost_budget_tokens: int                 │
└─────────────────────────────────────────┘
```

**Implementation:** `backend/core/context.py`

---

## 4. Document Ingestion (Antigravity Router)

### 4.1 Classification Logic

```
IF source is "Immutable Truth" (Class A):
   → Docling (IBM) for high-fidelity extraction
   → Table reconstruction with TableFormer
   → Bounding box coordinates for provenance
   
ELIF source is "Ephemeral Chatter" (Class B):
   → Unstructured.io for semantic chunking
   → Header-based splitting
   → Metadata extraction
   
ELIF source is "Operational Telemetry" (Class C):
   → Pandas/native for structured data
   → Direct vector conversion
   → Time-series handling
```

### 4.2 File Type Mappings

| Class | Extensions | Engine |
|-------|------------|--------|
| **A (Truth)** | .pdf, .scidoc | Docling |
| **B (Chatter)** | .docx, .pptx, .eml, .html, .md | Unstructured |
| **C (Ops)** | .csv, .parquet, .json, .log | Pandas |

### 4.3 Metadata Fields

Every ingested document includes:

- `provenance_id`: Link to source file + page/location
- `vector_triad`: `{entity, action, context}`
- `decay_rate`: 0.0 (permanent) to 1.0 (ephemeral)
- `classification`: Class A/B/C designation

**Implementation:** `backend/etl/antigravity_router.py`

---

## 5. Tri-Search™ (Hybrid Memory Search)

### 5.1 Search Modes Combined

1. **Keyword Search** — BM25/inverted index
2. **Vector Search** — pgvector cosine similarity
3. **Graph Search** — Graphiti relationship traversal

### 5.2 Fusion Algorithm

```python
# Reciprocal Rank Fusion (RRF)
def rrf_score(ranks, k=60):
    return sum(1.0 / (k + rank) for rank in ranks)
```

### 5.3 API Endpoint

```
POST /api/v1/memory/search
{
    "query": "string",
    "search_type": "similarity" | "hybrid" | "graph",
    "user_id": "string",
    "limit": 10
}
```

**Implementation:** `backend/memory/client.py` → `search_memory()`

---

## 6. Voice & Avatar System

### 6.1 Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Voice Input** | Azure Speech SDK | Speech-to-text |
| **Voice Output** | Azure VoiceLive | Real-time TTS |
| **Avatar Video** | aiortc + WebRTC | Video avatar rendering |
| **Signaling** | FastAPI WebSocket | SDP/ICE exchange |

### 6.2 Architecture

```
Frontend ←→ WebSocket ←→ VoiceLive Service ←→ Azure Speech
    ↓           ↓
 WebRTC ←→ Signaling Server ←→ Avatar Renderer
```

**Implementation:**

- `backend/voice/voicelive_service.py`
- `backend/voice/webrtc_signaling.py`
- `frontend/src/components/AvatarCall.tsx`

---

## 7. OSS Dependencies

### 7.1 Core Framework

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | ≥0.109.0 | REST API framework |
| `uvicorn` | ≥0.27.0 | ASGI server |
| `pydantic` | ≥2.5.0 | Data validation |
| `langchain` | ≥0.1.0 | Agent framework base |
| `langgraph` | ≥0.0.20 | Agent graph execution |

### 7.2 Memory & Orchestration

| Package | Version | Purpose |
|---------|---------|---------|
| `zep-python` | ≥2.0.0 | Memory service client |
| `graphiti-core` | ≥0.2.0 | Knowledge graph |
| `temporalio` | ≥1.4.0 | Workflow orchestration |
| `networkx` | ≥3.0.0 | Graph algorithms |

### 7.3 ETL & Document Processing

| Package | Version | Purpose |
|---------|---------|---------|
| `unstructured[all-docs]` | ≥0.12.0 | Document parsing |
| `python-magic` | ≥0.4.27 | File type detection |
| `Pillow` | ≥10.2.0 | Image processing |

### 7.4 Azure Services

| Package | Version | Purpose |
|---------|---------|---------|
| `azure-identity` | ≥1.15.0 | Auth management |
| `azure-ai-voicelive[aiohttp]` | ≥1.0.0 | Voice synthesis |
| `azure-cognitiveservices-speech` | ≥1.34.0 | Speech recognition |
| `msal` | ≥1.26.0 | Entra ID auth |

### 7.5 Observability

| Package | Version | Purpose |
|---------|---------|---------|
| `opentelemetry-*` | ≥1.22.0 | Distributed tracing |
| `azure-monitor-opentelemetry` | ≥1.2.0 | Azure Monitor export |

### 7.6 WebRTC

| Package | Version | Purpose |
|---------|---------|---------|
| `aiortc` | ≥1.6.0 | WebRTC implementation |
| `av` | ≥10.0.0 | Audio/video processing |

---

## 8. Infrastructure (Azure)

### 8.1 Bicep Modules

| Module | Resources |
|--------|-----------|
| `main.bicep` | Orchestrator, environment setup |
| `backend-aca.bicep` | Backend Container App |
| `worker-aca.bicep` | Temporal Worker Container App |
| `zep-aca.bicep` | Zep Memory Service |
| `temporal-aca.bicep` | Temporal Server |
| `keyvault.bicep` | Secrets management |
| `speech.bicep` | Azure Speech Service |
| `openai.bicep` | Azure OpenAI / AI Foundry |

### 8.2 On-Prem Equivalent (K8s)

| Azure | On-Prem Equivalent |
|-------|---------------------|
| Container Apps | Kubernetes + Ingress |
| PostgreSQL Flex | PostgreSQL (self-managed) |
| Key Vault | HashiCorp Vault |
| Azure Speech | Self-hosted TTS/STT |
| Azure Monitor | Prometheus + Grafana |

**Implementation:** `infra/k8s/` (11 manifests)

---

## 9. Frontend Architecture

### 9.1 Technology Stack

| Technology | Purpose |
|------------|---------|
| React 18 | UI framework |
| Vite | Build tool |
| TypeScript | Type safety |
| CSS Variables | Theming |

### 9.2 Key Components

| Component | Purpose |
|-----------|---------|
| `Chat.tsx` | Conversational interface |
| `Episodes.tsx` | Memory episode browser |
| `Stories.tsx` | AI-generated narratives |
| `AvatarCall.tsx` | Voice + video avatar |
| `SystemNavigator.tsx` | Admin/debug interface |

**Implementation:** `frontend/src/`

---

## 10. FedRAMP High Requirements

### 10.1 Security Controls Mapping

| FedRAMP Control | ctxgraph Implementation |
|-----------------|-------------------------|
| AC-2 (Account Management) | SecurityContext RBAC |
| AU-2 (Audit Events) | OpenTelemetry → SIEM |
| IA-2 (Identification) | Entra ID / OIDC integration |
| SC-8 (Transmission Confidentiality) | TLS 1.3 everywhere |
| SC-28 (Protection at Rest) | Database encryption |
| SI-2 (Flaw Remediation) | SBOM + Grype scanning |

### 10.2 On-Prem Deployment Changes

| Cloud Feature | On-Prem Alternative |
|---------------|---------------------|
| Azure AD | Keycloak / AD FS |
| Azure Key Vault | HashiCorp Vault |
| Azure Container Apps | Kubernetes |
| Azure PostgreSQL | Self-managed PostgreSQL |
| Azure Speech | OpenAI Whisper + Piper TTS |
| Azure OpenAI | vLLM + local models |

---

## 11. ctxgraph Repository Structure

```
ctxgraph/
├── backend/
│   ├── agents/           # LangGraph agents
│   ├── api/              # FastAPI routes + middleware
│   ├── core/             # Context schema, settings
│   ├── etl/              # Antigravity Router
│   ├── memory/           # Zep client
│   ├── voice/            # VoiceLive + WebRTC
│   ├── workflows/        # Temporal workflows
│   └── requirements.txt
├── frontend/
│   ├── src/
│   └── package.json
├── infra/
│   ├── k8s/              # Kubernetes manifests
│   ├── helm/             # Helm charts (new)
│   └── docker-compose.yml
├── docs/
│   ├── architecture/
│   ├── security/
│   └── operations/
├── scripts/
│   ├── deploy.sh
│   ├── rollback.sh
│   └── health-check.sh
├── .github/
│   └── workflows/
├── LICENSE               # MIT
├── README.md
└── SECURITY.md
```

---

## 12. Migration Checklist

### 12.1 Code Changes

- [ ] Remove all "Engram" branding
- [ ] Update package names to `ctxgraph`
- [ ] Replace Azure-specific auth with OIDC abstraction
- [ ] Add Keycloak integration option
- [ ] Create Helm charts for K8s deployment

### 12.2 Infrastructure Changes

- [ ] Create K8s-native deployment manifests
- [ ] Add Vault integration for secrets
- [ ] Create air-gapped container registry config
- [ ] Add offline model deployment scripts

### 12.3 Documentation Changes

- [ ] Update all docs for ctxgraph naming
- [ ] Add on-prem deployment guide
- [ ] Add FedRAMP compliance mapping
- [ ] Create operator runbook

---

## 13. Conclusion

**Yes, this is achievable.** The system is modular with clear separation:

1. **Brain** (agents) — portable, no cloud lock-in
2. **Spine** (Temporal) — self-hostable
3. **CtxGraph** (Zep) — self-hostable or Cloud
4. **Security** — abstracted via SecurityContext
5. **Infrastructure** — K8s manifests already exist

**Effort Estimate:** 2-3 weeks to create clean ctxgraph fork with:

- Rebranded codebase
- Helm charts
- On-prem auth integration
- Air-gapped deployment scripts
- FedRAMP documentation

---

*Document Version: 1.0*  
*Created: 2026-01-10*  
*Owner: Zimax Networks LC*
