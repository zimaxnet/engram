---
layout: default
title: Navigation UI Enterprise Deployment Strategy
---

# Navigation UI Enterprise Deployment Strategy for Engram Platform

## Executive Summary

This document outlines Zimax Networks LC's strategy for deploying the Engram Navigation UI in customer environments (dev/test/UAT/prod). The Navigation UI is the **critical integration layer** that ties together all Engram components—Temporal workflows, Zep memory, Unstructured ETL, PostgreSQL/Blob Storage—into a unified enterprise interface. This plan addresses enterprise requirements including frontend-backend integration, navigation patterns, user flows, authentication/RBAC, performance optimization, and NIST AI RMF compliance from a UI/UX perspective.

**Key Decision**: React-based Navigation UI (TreeNav) with FastAPI backend integration for customer environments to enable:
- Unified interface for all Engram capabilities
- Real-time workflow orchestration visibility
- Provenance-first memory search and exploration
- Enterprise-grade authentication and RBAC
- Seamless integration with customer identity providers
- Responsive, accessible, and performant user experience

---

## 1. Navigation UI Architecture: Frontend-Backend Integration

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│              Engram Navigation UI (React)                │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  TreeNav     │  │   Routes     │  │   Pages      │ │
│  │  Component   │  │  (React      │  │  (Feature    │ │
│  │              │  │   Router)    │  │   Views)     │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                 │                  │          │
│         └─────────────────┼──────────────────┘         │
│                           │                             │
│                  ┌─────────▼─────────┐                  │
│                  │   Service Layer   │                  │
│                  │  (api.ts, bau.ts, │                  │
│                  │   metrics.ts, etc)│                  │
│                  └─────────┬─────────┘                  │
│                           │                             │
└───────────────────────────┼─────────────────────────────┘
                            │
                            │ HTTP/REST
                            │
┌───────────────────────────▼─────────────────────────────┐
│          FastAPI Backend (Python)                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│
│  │  Agents  │  │  Chat    │  │  Memory  │  │Workflows ││
│  │  Router  │  │  Router  │  │  Router  │  │  Router  ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘│
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│
│  │   BAU    │  │ Metrics  │  │Validation│  │   ETL    ││
│  │  Router  │  │  Router  │  │  Router   │  │  Router  ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘│
│                                                          │
│  ┌──────────┐  ┌──────────┐                            │
│  │  Admin   │  │  Health  │                            │
│  │  Router  │  │  Router  │                            │
│  └──────────┘  └──────────┘                            │
│                                                          │
└─────────────────────────────────────────────────────────┘
                            │
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Temporal   │    │     Zep      │    │ Unstructured │
│  (Workflows) │    │   (Memory)   │    │    (ETL)     │
└──────────────┘    └──────────────┘    └──────────────┘
```

### Navigation Structure (TreeNav Component)

The Navigation UI uses a hierarchical tree structure organized by functional domain:

| Section | Sub-Items | Backend Integration | Purpose |
|---------|-----------|---------------------|---------|
| **Cognition (Agents)** | Overview, Elena, Marcus | `/api/v1/agents` | Agent selection and configuration |
| **Chat & Voice** | Chat (Episodic), Voice Interaction | `/api/v1/chat` | Real-time conversation interface |
| **Ingestion** | Connectors, Document Upload, Progress | `/api/v1/etl/ingest` | Document intake and processing |
| **Evidence & Validation** | Golden Thread Runner, Evidence & Telemetry | `/api/v1/validation`, `/api/v1/metrics` | Quality assurance and monitoring |
| **BAU** | BAU Hub | `/api/v1/bau` | Business-as-usual workflows |
| **Memory (Provenance-First)** | Search, Episodes, Knowledge Graph | `/api/v1/memory` | Memory exploration and search |
| **Workflows (Durable Spine)** | Active, History, Signals | `/api/v1/workflows` | Temporal workflow management |
| **Settings** | General | `/api/v1/admin/settings` | System configuration |
| **Admin** | Users, System Health | `/api/v1/admin` | Administrative functions |

### Frontend-Backend Integration Pattern

**Service Layer Architecture**:

1. **API Client (`api.ts`)**: Centralized HTTP client with:
   - Authentication token management
   - Error handling and retry logic
   - Request/response transformation
   - Type-safe interfaces

2. **Feature Services**: Domain-specific service wrappers:
   - `bau.ts`: BAU workflow management
   - `metrics.ts`: Evidence telemetry
   - `validation.ts`: Golden Thread validation
   - `workflowDetail.ts`: Workflow detail views
   - `ingestion.ts`: Document ingestion

3. **Page Components**: React components that:
   - Call service layer functions
   - Manage local state
   - Handle user interactions
   - Navigate between routes

**Integration Flow**:
```
User Action (Click/Input)
    │
    ▼
Page Component (React)
    │
    ▼
Service Layer (TypeScript)
    │
    ▼
API Client (HTTP Request)
    │
    ▼
FastAPI Router (Python)
    │
    ▼
Backend Service (Temporal/Zep/Unstructured)
    │
    ▼
Response → Service Layer → Page Component → UI Update
```

---

## 2. Navigation Patterns and User Flows

### Primary User Flows

#### Flow 1: Document Ingestion → Memory → Chat

```
1. User navigates to "Ingestion" → "Document Upload"
2. User uploads document via SourcesPage
3. Document processed by Unstructured (ETL Router)
4. Chunks indexed to Zep (Memory Router)
5. User navigates to "Memory" → "Search"
6. User searches for content from ingested document
7. User navigates to "Chat" → Starts conversation with Elena
8. Elena retrieves relevant memory via Memory Router
9. User views workflow execution in "Workflows" → "Active"
```

**Backend Integration Points**:
- `/api/v1/etl/ingest` (Unstructured processing)
- `/api/v1/memory/search` (Zep retrieval)
- `/api/v1/chat` (Agent conversation)
- `/api/v1/workflows` (Temporal orchestration)

#### Flow 2: BAU Workflow → Validation → Evidence

```
1. User navigates to "BAU" → "BAU Hub"
2. User starts "Intake & triage" workflow
3. Temporal workflow started via `/api/v1/bau/flows/{flow_id}/start`
4. User navigates to "Workflows" → "Active" to monitor
5. User navigates to "Evidence & Validation" → "Golden Thread Runner"
6. User triggers validation run via `/api/v1/validation/run`
7. User views results and evidence bundle
8. User navigates to "Evidence & Telemetry" for operational metrics
```

**Backend Integration Points**:
- `/api/v1/bau/flows/{flow_id}/start` (BAU workflow initiation)
- `/api/v1/workflows/{workflow_id}` (Temporal workflow status)
- `/api/v1/validation/run` (Golden Thread execution)
- `/api/v1/metrics/evidence` (Operational telemetry)

#### Flow 3: Memory Exploration → Knowledge Graph → Workflow Detail

```
1. User navigates to "Memory" → "Search"
2. User searches for specific topic via `/api/v1/memory/search`
3. User views search results with provenance metadata
4. User navigates to "Memory" → "Knowledge Graph"
5. User explores semantic relationships
6. User navigates to "Workflows" → "Active"
7. User clicks workflow to view detail
8. User views workflow steps, signals, and context via `/api/v1/workflows/{workflow_id}`
```

**Backend Integration Points**:
- `/api/v1/memory/search` (Zep semantic search)
- `/api/v1/memory/episodes` (Episodic memory)
- `/api/v1/workflows/{workflow_id}` (Temporal workflow detail)

### Navigation State Management

**Route-Based State**:
- React Router manages navigation state
- URL parameters for workflow IDs, session IDs, etc.
- Deep linking support for sharing specific views

**Component State**:
- Local component state for UI interactions
- Service layer caching for API responses
- Optimistic updates for better UX

**Global State** (Future):
- Agent selection (currently prop-drilled)
- User preferences
- Authentication context

---

## 3. Enterprise Deployment Considerations

### Frontend Deployment Options

| Option | Description | Use Case | Engram Recommendation |
|--------|-------------|----------|----------------------|
| **Static Site Hosting** | Pre-built React app served from CDN | Production, high traffic | ✅ **Recommended** - Azure Static Web Apps |
| **Server-Side Rendering (SSR)** | React rendered on server | SEO, initial load performance | Consider for public-facing pages |
| **Container Deployment** | React app in container | Custom deployment requirements | Alternative for on-premises |

**Current Implementation**: Static site (Vite build) → Azure Static Web Apps

### Backend Integration Architecture

**API Gateway Pattern**:
- Frontend calls single API endpoint (`/api/v1/*`)
- FastAPI routes handle domain-specific logic
- Backend services (Temporal, Zep, Unstructured) abstracted behind API

**Authentication Flow**:
```
1. User logs in via Microsoft Entra ID (or customer IdP)
2. Frontend receives JWT token
3. Token stored in localStorage (or secure cookie)
4. API Client includes token in Authorization header
5. FastAPI middleware validates token
6. SecurityContext passed to route handlers
```

**RBAC Integration**:
- User roles determined from token claims
- Frontend shows/hides navigation items based on role
- Backend enforces permissions at API level
- Memory search results filtered by tenant/role

### Performance Optimization

**Frontend Optimizations**:
1. **Code Splitting**: Route-based code splitting via React Router
2. **Lazy Loading**: Components loaded on demand
3. **API Response Caching**: Service layer caches frequently accessed data
4. **Optimistic Updates**: UI updates immediately, syncs with backend

**Backend Optimizations**:
1. **Response Caching**: LRU cache for Evidence Telemetry (60s TTL)
2. **Pagination**: List endpoints support limit/offset
3. **Connection Pooling**: Database connections pooled
4. **Async Processing**: Long-running tasks handled asynchronously

**CDN Configuration**:
- Static assets (JS, CSS, images) served from CDN
- API requests go directly to FastAPI backend
- Cache headers configured for static assets

---

## 4. Integration with Engram Components

### Temporal Workflow Integration

**Navigation Points**:
- "Workflows" → "Active": List running workflows
- "Workflows" → "History": List completed workflows
- "Workflows" → "{workflow_id}": Workflow detail view

**Backend Integration**:
- `/api/v1/workflows` → Temporal client queries
- `/api/v1/workflows/{workflow_id}/signal` → Temporal signal API
- `/api/v1/workflows/{workflow_id}/cancel` → Temporal cancellation API

**UI Features**:
- Real-time workflow status updates (polling every 5s)
- Workflow step visualization
- Signal/query interface
- Trace ID linking to Evidence Telemetry

### Zep Memory Integration

**Navigation Points**:
- "Memory" → "Search": Semantic search with provenance
- "Memory" → "Episodes": Episodic memory (conversation history)
- "Memory" → "Knowledge Graph": Semantic memory visualization

**Backend Integration**:
- `/api/v1/memory/search` → Zep search API
- `/api/v1/memory/episodes` → Zep session API
- `/api/v1/memory/facts` → Zep Graphiti API

**UI Features**:
- Provenance metadata display (filename, source, tenant, sensitivity)
- Confidence scores and retrieval quality indicators
- Link to source documents in Blob Storage
- Entity relationship visualization

### Unstructured ETL Integration

**Navigation Points**:
- "Ingestion" → "Connectors": Source management
- "Ingestion" → "Document Upload": Direct upload
- "Ingestion" → "Progress": Ingestion queue status

**Backend Integration**:
- `/api/v1/etl/ingest` → Unstructured processing
- Ingestion queue management (future: dedicated queue endpoint)

**UI Features**:
- Source configuration wizard
- Document upload with drag-and-drop
- Real-time ingestion progress
- Parse success/failure indicators

### PostgreSQL/Blob Storage Integration

**Navigation Points**:
- Memory search results link to source documents
- Evidence bundles downloadable from Golden Thread
- Workflow artifacts stored in Blob Storage

**Backend Integration**:
- PostgreSQL: Zep memory queries (abstracted via Memory Router)
- Blob Storage: Document storage (abstracted via ETL Router)

**UI Features**:
- Document preview (future)
- Download links for evidence bundles
- Storage tier indicators (Hot/Cool/Archive)

---

## 5. NIST AI RMF Compliance: UI/UX Perspective

### Framework Mapping

| NIST AI RMF Function | UI Implementation | Navigation Integration | Evidence |
|----------------------|-------------------|----------------------|----------|
| **Govern** | Settings page, Admin section | `/settings/general`, `/admin/users` | Configuration UI, user management |
| **Map** | Provenance display, metadata chips | Memory search results, workflow detail | Tenant tags, sensitivity labels |
| **Measure** | Evidence Telemetry dashboard | `/evidence` | Metrics visualization, alerts |
| **Manage** | Workflow controls, validation runner | `/workflows`, `/validation/golden-thread` | Signal interface, validation UI |

### UI Controls for Compliance

**Data Classification Display**:
- Sensitivity tags (Silver, Gold, Platinum) shown in memory search
- Tenant scoping visible in all memory results
- RBAC indicators in navigation (role-based visibility)

**Audit Trail Access**:
- Admin → System Health shows audit logs
- Workflow detail shows execution history
- Evidence bundles include trace IDs

**Access Control UI**:
- Role-based navigation item visibility
- Permission checks before API calls
- Error messages for unauthorized actions

**Transparency Features**:
- Provenance metadata always visible
- Confidence scores for AI-generated content
- Source citations in chat responses
- Workflow execution traceability

---

## 6. Authentication and RBAC Integration

### Authentication Architecture

**Current Implementation**:
- JWT tokens from Microsoft Entra ID
- Token stored in localStorage
- API Client includes token in requests
- FastAPI middleware validates token

**Enterprise Requirements**:
- Support customer IdP (Okta, Ping, etc.)
- SSO integration
- Session management
- Token refresh

### RBAC Implementation

**Role-Based Navigation**:
- Navigation items filtered by user role
- Admin section only visible to admins
- Settings access controlled by role

**API-Level Enforcement**:
- FastAPI middleware checks permissions
- Memory search filtered by tenant/role
- Workflow access controlled by permissions

**UI Indicators**:
- Role badges in user profile
- Permission warnings for restricted actions
- Graceful degradation for unauthorized features

---

## 7. Operational Responsibilities

### Zimax Networks LC Support Model

**For Customer Environments (dev/test/UAT/prod)**:

| Responsibility | Zimax Networks LC | Customer |
|----------------|------------------|----------|
| Frontend deployment | ✅ Build & deploy to Static Web Apps | Infrastructure approval |
| Backend API deployment | ✅ FastAPI container deployment | Infrastructure approval |
| Navigation customization | ✅ Role-based navigation configuration | Role definitions |
| Authentication integration | ✅ IdP integration & SSO setup | IdP credentials |
| Performance optimization | ✅ CDN configuration, caching | CDN provider selection |
| UI/UX updates | ✅ Feature updates & bug fixes | Requirements definition |
| Monitoring & alerting | ✅ Frontend error tracking | Alert response |
| Accessibility compliance | ✅ WCAG 2.1 AA compliance | Accessibility requirements |
| Browser compatibility | ✅ Testing & support | Browser policy |

**Dedicated Resources Required**:
- **Frontend Engineer**: React development, UI/UX optimization
- **Backend Engineer**: FastAPI integration, API design
- **DevOps Engineer**: Deployment, CDN configuration, monitoring
- **UX Designer**: User flows, accessibility, enterprise patterns

---

## 8. Implementation Roadmap

### Phase 1: Foundation (Months 1-2)
- [ ] Document navigation architecture and user flows
- [ ] Audit API integration completeness
- [ ] Identify missing backend endpoints
- [ ] Design authentication/SSO integration
- [ ] Plan RBAC implementation

### Phase 2: Integration Completion (Months 2-3)
- [ ] Complete missing API integrations
- [ ] Implement authentication/SSO
- [ ] Add RBAC to navigation and API
- [ ] Optimize API response caching
- [ ] Add error handling and retry logic

### Phase 3: Enterprise Features (Months 3-4)
- [ ] Implement role-based navigation filtering
- [ ] Add audit log UI integration
- [ ] Enhance provenance display
- [ ] Add accessibility features (WCAG 2.1 AA)
- [ ] Performance optimization (code splitting, lazy loading)

### Phase 4: Compliance & Documentation (Months 4-5)
- [ ] Map NIST AI RMF controls to UI features
- [ ] Create user documentation
- [ ] Prepare security assessment documentation
- [ ] Train support team
- [ ] Create deployment runbooks

### Phase 5: Production Deployment (Months 5-6)
- [ ] Deploy to customer dev environment
- [ ] Validate authentication/SSO
- [ ] Test RBAC enforcement
- [ ] Performance testing
- [ ] Gradual rollout to test/UAT/prod

---

## 9. Risk Mitigation

### Risk: API Integration Gaps

**Mitigation**:
- Comprehensive API audit
- Service layer abstraction for easy updates
- Mock data for development/testing
- Integration tests for all API calls

### Risk: Performance Degradation

**Mitigation**:
- Code splitting and lazy loading
- API response caching
- CDN for static assets
- Performance monitoring and alerts

### Risk: Authentication/SSO Failures

**Mitigation**:
- Fallback authentication methods
- Token refresh logic
- Session timeout handling
- Error messages for auth failures

### Risk: RBAC Enforcement Gaps

**Mitigation**:
- Backend enforcement (not just frontend)
- Regular security audits
- Permission testing
- Audit logging of access attempts

---

## 10. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Page load time (First Contentful Paint) | < 1.5s | Web Vitals API |
| API response time (p95) | < 500ms | Application Insights |
| Navigation click-to-render | < 200ms | User interaction tracking |
| API error rate | < 1% | Error tracking |
| Authentication success rate | > 99.9% | Auth logs |
| RBAC enforcement accuracy | 100% | Security audit |
| Accessibility score (Lighthouse) | > 90 | Automated testing |
| User satisfaction (NPS) | > 50 | User surveys |

---

## 11. Next Steps

1. **Approve this strategy** for customer environment deployment
2. **Allocate resources** for Frontend Engineer, Backend Engineer, DevOps Engineer, UX Designer
3. **Begin Phase 1** implementation (API audit, authentication design)
4. **Engage with customer** for IdP integration requirements
5. **Schedule security assessment** preparation timeline

---

## References

- [React Router Documentation](https://reactrouter.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Azure Static Web Apps](https://learn.microsoft.com/azure/static-web-apps/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)

