---
layout: default
title: "Engram UI Design Reference"
parent: "Strategy"
---

# Engram UI Design Reference

**Last Updated:** December 15, 2025  
**Purpose:** Quick reference mapping UI mockups to implementation status, frontend pages, backend endpoints, and tests.

---

## Mockup Inventory

Primary assets live in `docs/assets/images/` unless noted.

### PNG Mockups
- bau-hub.png — BAU Hub dashboard
- context-ingestion.png — Sources/ingestion dashboard
- evidence-telemetry-panel.png — Evidence & telemetry view
- golden-thread-validation.png — Golden Thread runner/results
- memory-search-provenance.png — Memory search with provenance
- temporal-workflow.png — Temporal workflow detail
- voice-interaction-flow.png — Voice interaction flow
- workflow-detail-durable-spine.png — Workflow detail
- engram-platform-architecture.png — Platform architecture
- engram-logo.png / engram-favicon.png — Branding assets

### SVG Mockups
- agent-workflow-diagram.svg — Agent handoff flow
- context-schema.svg — Context schema
- elena-portrait.svg / marcus-portrait.svg — Portraits
- engram-logo.svg — Logo vector
- engram-platform-architecture.svg — Architecture vector

Frontend concept copies (for reference) live in `frontend/public/assets/images/` (concept-*.png, portraits, platform-architecture.png, temporal-workflow.png).

---

## Implementation Status Matrix

### ✅ Fully Implemented

**BAU Hub** (bau-hub.png)  
- Frontend: frontend/src/pages/BAU/BAUHub.tsx  
- Backend: backend/api/routers/bau.py  
- Endpoints: GET /api/v1/bau/flows, GET /api/v1/bau/artifacts, POST /api/v1/bau/flows/{flow_id}/start  
- Tests: BAUHub.test.tsx; backend/tests/test_bau_router.py; .dev/test-suites/e2e/bau-flow.spec.ts  

**Evidence & Telemetry** (evidence-telemetry-panel.png)  
- Frontend: frontend/src/pages/Evidence/EvidenceTelemetry.tsx  
- Backend: backend/api/routers/metrics.py  
- Endpoint: GET /api/v1/metrics/evidence  
- Tests: EvidenceTelemetry.test.tsx; backend/tests/test_metrics_router.py; e2e/evidence-drill.spec.ts  

**Golden Thread Validation** (golden-thread-validation.png)  
- Frontend: frontend/src/pages/Validation/GoldenThreadRunner.tsx  
- Backend: backend/api/routers/validation.py  
- Endpoints: GET /validation/datasets, GET /validation/runs/latest, POST /validation/run, GET /validation/runs/{run_id}  
- Tests: GoldenThreadRunner.test.tsx; backend/tests/test_validation_router.py; e2e/golden-thread.spec.ts  

**Workflow Detail** (workflow-detail-durable-spine.png)  
- Frontend: frontend/src/pages/Workflows/WorkflowDetail.tsx  
- Backend: backend/api/routers/workflows.py  
- Endpoints: GET /workflows, GET /workflows/{id}, POST /workflows/{id}/signal  
- Tests: WorkflowDetail.test.tsx; backend/tests/test_workflows_e2e.py; e2e/workflow-signal.spec.ts  

**Memory Search** (memory-search-provenance.png)  
- Frontend: frontend/src/pages/Memory/Search.tsx, Episodes.tsx  
- Backend: backend/api/routers/memory.py  
- Endpoints: POST /memory/search, GET /memory/episodes, POST /memory/facts  
- Tests: backend/tests/test_memory_operations.py  

**Voice Interaction** (voice-interaction-flow.png)  
- Frontend: frontend/src/pages/Voice/VoiceInteractionPage.tsx; components/VoiceChat/VoiceChat.tsx  
- Backend: WebSocket endpoint (voice)  
- Tests: VoiceInteractionPage.test.tsx; VoiceChat.test.tsx; .dev/test-suites/e2e/voice-interaction.spec.ts  

### ✅ Recently Completed (formerly mock)

**Context Ingestion / Sources** (context-ingestion.png)  
- Frontend: frontend/src/pages/Sources/SourcesPage.tsx  
- Service: frontend/src/services/ingestion.ts  
- Backend: backend/api/routers/etl.py with JSON-backed sources and queue  
- Endpoints: POST /api/v1/etl/ingest; GET/POST /etl/sources; GET /etl/sources/{id}; GET /etl/queue  
- Status: Connectors persist to backend/data/etl_state.json; queue auto-progresses to completed and updates docs/health.

**Admin Users & Audit** (concept-admin.png)  
- Frontend: frontend/src/pages/Admin/UserManagement.tsx, SystemHealth.tsx  
- Backend: backend/api/routers/admin.py with JSON-backed users/audit/settings  
- Endpoints: GET/PUT /admin/settings; GET /admin/users; GET /admin/audit  
- Status: Data stored in backend/data/admin_state.json with audit trail on settings updates.

**Knowledge Graph** (concept-graph.png)  
- Frontend: frontend/src/pages/Memory/KnowledgeGraph.tsx (SVG graph + list)  
- Backend: backend/api/routers/memory.py `/memory/graph`  
- Status: Renders fact/entity nodes and metadata edges; filterable by query.

### 📘 Reference
- engram-platform-architecture.png / .svg — architecture reference
- temporal-workflow.png — workflow architecture

---

## Backend Data Sources (today)
- Chat / Memory: Zep (real)
- Workflows: Temporal (real)
- Upload: Unstructured → Zep (real)
- BAU: Config-driven (intentional)
- Metrics: Partly mocked
- Connectors: JSON-backed with progress
- Users/Audit: JSON-backed

---

## Priority Roadmap

**P1 — Context Ingestion (Sources)**
1) Add backend connector APIs: GET/POST /etl/sources, GET /etl/sources/{id}, GET /etl/queue.  
2) Persist connector state (DB or in-memory with TODO to persist).  
3) Frontend: replace mock functions in services/ingestion.ts with real calls; add upload progress.
4) Add E2E test for upload + source list.

**P2 — Admin Users & Audit**
1) Backend: replace _mock_users/_mock_audit_logs with real store/log sink.  
2) Frontend already wired; once backend returns real data, UI becomes live.

**P3 — Knowledge Graph**
1) Backend: add GET /memory/graph returning nodes/edges (filter by user/tenant).  
2) Frontend: render graph (e.g., React Flow/Cytoscape) in KnowledgeGraph.tsx.  
3) Add tests.

---

## Quick Frontend → Backend Map
- BAU: /api/v1/bau/* (flows, artifacts, start)
- Sources: /api/v1/etl/ingest (upload) + new /etl/sources, /etl/queue (to add)
- Evidence: /api/v1/metrics/evidence
- Validation: /api/v1/validation/*
- Workflows: /api/v1/workflows, /workflows/{id}, /workflows/{id}/signal
- Memory: /api/v1/memory/search, /memory/episodes, /memory/facts (needs /memory/graph)
- Admin: /api/v1/admin/settings (real); /admin/users, /admin/audit (mock)
- Voice: WS voice endpoint

---

## Mock Data Cleanup Checklist
- [x] Replace services/ingestion.ts mocks with real connector APIs
- [x] Implement /etl/sources and /etl/queue backend endpoints
- [ ] Add upload progress UI and tests
- [x] Replace _mock_users and _mock_audit_logs with real data sources
- [x] Implement /memory/graph and real graph UI

---

## Test Coverage Snapshot
- BAU: FE ✅ / BE ✅ / E2E ✅
- Evidence: FE ✅ / BE ✅ / E2E ✅
- Golden Thread: FE ✅ / BE ✅ / E2E ✅
- Workflows: FE ✅ / BE ✅ / E2E ✅
- Memory: BE ✅ (search/episodes) / FE partial / E2E —
- Sources: BE (upload) ✅ / FE mock / E2E —
- Admin: FE wired / BE mock / E2E —
- Voice: FE ✅ / BE WS ✅ / E2E ✅

---

## Developer Workflow
1) Open the mockup listed above.  
2) Confirm page, route, nav entry, service call, backend endpoint, and tests.  
3) If mock data exists, implement real endpoint, wire service, add tests, and check off the checklist.
