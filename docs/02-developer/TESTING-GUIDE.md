---
layout: default
title: "Engram Platform - Complete Testing Guide"
parent: "Developer Guide"
---

# Engram Platform - Complete Testing Guide


## Test Environment
- **Frontend**: https://engram.work
- **Backend API**: https://engram-api.calmgrass-018b2019.eastus2.azurecontainerapps.io
- **API Base**: `/api/v1`

## Test Checklist

### 1. Health & Readiness ✅
- [ ] Health endpoint
- [ ] Readiness endpoint

### 2. Agents API 🤖
- [ ] List all agents
- [ ] Get agent details (Elena)
- [ ] Get agent details (Marcus)
- [ ] Switch active agent

### 3. Chat API 💬
- [ ] Send text message
- [ ] WebSocket chat connection
- [ ] Session management
- [ ] Agent-specific responses

### 4. Memory API 🧠
- [ ] Search memory
- [ ] List episodes
- [ ] Add facts

### 5. Workflows API ⚡
- [ ] List workflows
- [ ] Get workflow details
- [ ] Start conversation
- [ ] Send workflow signal
- [ ] Workflow history

### 6. Frontend UI 🎨
- [ ] Page loads correctly
- [ ] Agent selection (Elena/Marcus)
- [ ] Chat panel functionality
- [ ] Visual panel metrics
- [ ] Tree navigation

---

## Test Execution

Let's walk through each category systematically.

## Golden Thread Validation (E2E proof)

![Golden Thread validation suite](/assets/images/golden-thread-validation.png)

- Deterministic run over a seeded dataset (anchors: gh-pages, ingestion, /api/v1/etl/ingest).
- Eight checks cover auth gate, ingest, memory hit, workflow ordering, and episode transcript.
- Use as a release gate per environment; re-run failed checks only when iterating fixes.

