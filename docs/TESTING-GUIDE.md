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

### 4. Voice API 🎤
- [ ] Speech-to-Text (transcribe)
- [ ] Text-to-Speech (synthesize)
- [ ] Voice WebSocket connection
- [ ] Real-time transcription
- [ ] Voice configuration

### 5. Memory API 🧠
- [ ] Search memory
- [ ] List episodes
- [ ] Add facts

### 6. Workflows API ⚡
- [ ] List workflows
- [ ] Get workflow details
- [ ] Start conversation
- [ ] Send workflow signal
- [ ] Workflow history

### 7. Frontend UI 🎨
- [ ] Page loads correctly
- [ ] Agent selection (Elena/Marcus)
- [ ] Chat panel functionality
- [ ] Visual panel metrics
- [ ] Voice controls
- [ ] Tree navigation

---

## Test Execution

Let's walk through each category systematically.

