# Tasks

- [x] Investigate Episodes Loading Issue <!-- id: 14 -->
  - [x] Locate `Episodes.tsx` and analyze data fetching <!-- id: 15 -->
  - [x] Inspect backend `list_episodes` logic in `memory/client.py` <!-- id: 16 -->
  - [x] Inspect backend `list_episodes` logic in `memory/client.py` <!-- id: 16 -->
  - [x] Reproduce or identify the failure <!-- id: 17 -->
  - [x] Fix the infinite spinner / loading state <!-- id: 18 -->
  - [x] Verify fix <!-- id: 19 -->

- [x] Fix Backend Deployment
  - [x] Add health check to docker-compose
  - [x] Fix `test_etl_router.py` monkeypatch error
  - [x] Diagnose Bicep `BCP037` errors
  - [x] Fix `authConfig`, `sid`, `defender` properties in Bicep
  - [x] Fix FastMCP initialization crash (Defensive Wrap)
  - [x] Fix MCP name collision (`mcp.py` -> `mcp_server.py`) and restore functionality
  - [x] Fix Dockerfile missing system dependencies (`libmagic1`) <!-- id: 24 -->

- [x] Research Featureform <!-- id: 20 -->
  - [x] Analyze Featureform Architecture (Virtual Store, Lineage) <!-- id: 21 -->
  - [x] Synthesize "Virtual Context Store" proposal for Engram <!-- id: 22 -->
  - [x] Create Virtual Context Store Diagram JSON Spec <!-- id: 23 -->
  - [x] Refine Diagram Spec (Reverted to V1) <!-- id: 25 -->
  - [x] Refine Diagram Spec (Reverted to V1) <!-- id: 25 -->
  - [x] Research MCP Java SDK (Enterprise Connectors) <!-- id: 26 -->
  - [x] Integrate "Dual-Stack" Architecture Strategy <!-- id: 27 -->

- [x] Verify E2E Tests
  - [x] Fix Frontend build errors (TS6133, TS2322)
  - [x] Diagnose persistent E2E health check failure (Missing system deps)
  - [x] Verify local container startup (libmagic1 fix) <!-- id: 28 -->

- [x] Implement Virtual Context Store <!-- id: 29 -->
  - [x] Scaffold `backend/context` module (Registry & Store) <!-- id: 30 -->
  - [x] Implement Context Providers (Zep, Postgres) <!-- id: 31 -->
  - [x] Create Context Definition Decorators (`@engram.context`) <!-- id: 32 -->
  - [x] Expose Context via MCP <!-- id: 33 -->

- [ ] Dogfood Virtual Context Store <!-- id: 34 -->
  - [ ] Ingest Artifacts (Plans, Research) into Memory <!-- id: 35 -->
  - [ ] Define `engram_project_state` Context Definition <!-- id: 36 -->
  - [ ] Verify Agents can reflect on Engram's own architecture <!-- id: 37 -->
