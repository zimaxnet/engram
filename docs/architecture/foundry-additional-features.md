---
layout: default
title: Additional Foundry Features We Can Leverage
parent: Architecture
nav_order: 11
---

# Additional Foundry Features We Can Leverage

> **Last Updated**: January 2026  
> **Status**: Research & Planning  
> **Source**: [Azure AI Foundry Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry)

---

## Executive Summary

Azure AI Foundry offers **tremendous additional capabilities** beyond thread management that we can leverage to enhance Engram:

1. **Foundry IQ** - Enterprise data grounding via Azure AI Search
2. **Multi-Agent Orchestration** - Built-in agent collaboration workflows
3. **Foundry Tools** - Prebuilt production-ready capabilities
4. **Agent Catalog** - Discovery and management
5. **Microsoft 365 Integration** - Teams, Outlook, SharePoint
6. **Fine-Tuning** - Custom model training

---

## 1. Foundry IQ - Enterprise Data Grounding

### What It Is

**Foundry IQ** is powered by Azure AI Search and provides a smarter way to ground agents in enterprise data. Agents can connect to a **single knowledge base** to access multiple sources.

### Current State

**Engram's Tri-Search**:
- ✅ Keyword Search (Zep)
- ✅ Vector Search (pgvector)
- ✅ Graph Search (Knowledge Graph)

### How Foundry IQ Could Enhance

**Opportunity**: Use Foundry IQ as an **additional search layer** for enterprise documents

**Benefits**:
- ✅ Unified knowledge base (single source for multiple data sources)
- ✅ Azure AI Search integration (managed infrastructure)
- ✅ Automatic indexing
- ✅ Better response quality with broader data access

**Integration Approach**:
- Keep Engram's tri-search for episodic memory and conversation history
- Use Foundry IQ for **document-only** enterprise knowledge base
- Combine results using Reciprocal Rank Fusion (RRF)

**Implementation**:
```python
# Hybrid search: Engram tri-search + Foundry IQ
engram_results = await memory_client.search_memory(query)
foundry_iq_results = await foundry_iq_client.search(query)

# Combine using RRF
combined_results = reciprocal_rank_fusion([
    engram_results,
    foundry_iq_results
])
```

---

## 2. Multi-Agent Orchestration

### What It Is

Foundry supports **multi-agent workflows** where agents can:
- Have distinct roles
- Share memory/context
- Coordinate tasks
- Hand off to each other

### Current State

**Engram's Agent System**:
- ✅ Three agents (Elena, Marcus, Sage)
- ✅ Agent router with handoff detection
- ✅ Separate conversation threads per agent
- ✅ Agents can reference each other's work via memory search

### How Foundry Orchestration Could Enhance

**Opportunity**: Use Foundry's built-in multi-agent orchestration

**Benefits**:
- ✅ Built-in agent coordination
- ✅ Shared context management
- ✅ Automatic handoff handling
- ✅ Workflow visualization

**Integration Approach**:
- Create Foundry workflow with Elena, Marcus, and Sage
- Define handoff rules in Foundry
- Use Foundry's orchestration for complex multi-agent tasks
- Keep Engram's router for simple single-agent requests

**Use Cases**:
1. **Requirements → Project Planning**:
   - Elena creates requirements → Foundry orchestrates handoff → Marcus creates timeline

2. **Project → Story Creation**:
   - Marcus identifies need for documentation → Foundry orchestrates → Sage creates story

3. **Complex Multi-Step Tasks**:
   - Foundry coordinates all three agents for comprehensive project analysis

---

## 3. Foundry Tools - Prebuilt Capabilities

### What It Is

**Foundry Tools** provide ready-to-use APIs for:
- Content understanding
- Translation
- Speech processing
- Vision analysis
- Language processing

### Current State

**Engram's Tools**:
- ✅ Custom LangChain tools
- ✅ Microsoft Graph integration
- ✅ Memory search
- ✅ GitHub integration

### How Foundry Tools Could Enhance

**Opportunity**: Use Foundry Tools for **additional capabilities** we don't have

**Potential Tools**:
- **Translation** - Multi-language support
- **Vision Analysis** - Image/document understanding
- **Speech Processing** - Enhanced voice capabilities
- **Content Understanding** - Better document parsing

**Integration Approach**:
- Register Foundry Tools alongside Engram tools
- Agents can use both Foundry Tools and Engram tools
- Foundry Tools called via Foundry's tool execution framework

**Example**:
```python
# Elena can use both Engram and Foundry tools
tools = [
    # Engram tools
    send_email_tool,
    search_memory_tool,
    # Foundry tools
    foundry_translation_tool,
    foundry_vision_analysis_tool,
]
```

---

## 4. Agent Catalog & Discovery

### What It Is

Foundry provides an **Agent Catalog** for:
- Discovering available agents
- Managing agent definitions
- Versioning agents
- Sharing agents across projects

### Current State

**Engram's Agent Management**:
- ✅ Three agents defined in code
- ✅ Agent router for selection
- ✅ Agent info endpoint

### How Agent Catalog Could Enhance

**Opportunity**: Use Foundry's catalog for agent management

**Benefits**:
- ✅ Centralized agent definitions
- ✅ Version control for agents
- ✅ Agent discovery across projects
- ✅ Agent sharing and reuse

**Integration Approach**:
- Register Engram agents in Foundry catalog
- Use catalog for agent discovery
- Version agents via Foundry
- Share agents across Engram instances

---

## 5. Microsoft 365 Integration

### What It Is

Foundry enables publishing agents to:
- **Microsoft Teams** - Chat integration
- **Outlook** - Email integration
- **SharePoint** - Document integration
- **BizChat** - Business chat

### Current State

**Engram's Microsoft Integration**:
- ✅ Microsoft Graph API (email, OneDrive)
- ✅ Elena uses elena@zimax.net account
- ✅ Custom Graph client implementation

### How Foundry Integration Could Enhance

**Opportunity**: Use Foundry's native Microsoft 365 integration

**Benefits**:
- ✅ Native Teams integration
- ✅ Outlook add-in support
- ✅ SharePoint connector
- ✅ Simplified Graph API usage

**Integration Approach**:
- Publish Elena to Microsoft Teams
- Use Foundry's Outlook integration
- Leverage SharePoint connectors
- Keep custom Graph client for advanced features

**Use Cases**:
1. **Teams Bot**: Elena available as Teams bot
2. **Outlook Add-in**: Elena helps with email composition
3. **SharePoint**: Elena can access SharePoint documents directly

---

## 6. Fine-Tuning Capabilities

### What It Is

Foundry offers **fine-tuning** with:
- Expanded regional support
- Developer Tier (cost-effective)
- Custom model training
- Model versioning

### Current State

**Engram's Models**:
- ✅ Uses pre-trained models (GPT-5.2-chat, Claude, Gemini)
- ✅ No fine-tuning currently

### How Fine-Tuning Could Enhance

**Opportunity**: Fine-tune models for Engram-specific tasks

**Potential Use Cases**:
- Fine-tune for requirements analysis (Elena)
- Fine-tune for project management (Marcus)
- Fine-tune for technical documentation (Sage)

**Integration Approach**:
- Use Foundry's fine-tuning for specialized models
- Deploy fine-tuned models in Foundry
- Reference fine-tuned models in agent definitions

---

## 7. Vector Stores (Managed)

### What It Is

Foundry provides **managed vector stores** using Azure AI Search:
- Automatic embedding generation
- Managed infrastructure
- Project-scoped stores

### Current State

**Engram's Vector Storage**:
- ✅ Zep with pgvector
- ✅ Custom embedding client
- ✅ Tri-search with vector component

### How Foundry Vectors Could Enhance

**Opportunity**: Use Foundry vectors for **document-only** semantic search

**Benefits**:
- ✅ Managed infrastructure
- ✅ Automatic embedding generation
- ✅ Project-based isolation
- ✅ Less operational overhead

**Integration Approach**:
- Keep Zep vectors for episodic memory
- Use Foundry vectors for enterprise documents
- Combine results using RRF

**Decision**: **Don't use initially** - Zep vectors work well. Consider for document-only use case later.

---

## Implementation Roadmap

### Phase 1: Current (Thread Management) ✅

- ✅ Foundry thread management
- ✅ Elena migration to Foundry
- ✅ Tool endpoints

### Phase 2: Foundry IQ (Next)

**Goal**: Add Foundry IQ for enterprise document search

**Tasks**:
1. Create Foundry IQ knowledge base
2. Connect to Azure AI Search
3. Integrate with Engram's search
4. Combine results using RRF

**Timeline**: 2-3 weeks

### Phase 3: Multi-Agent Orchestration

**Goal**: Use Foundry workflows for complex multi-agent tasks

**Tasks**:
1. Create Foundry workflow with Elena, Marcus, Sage
2. Define handoff rules
3. Integrate with Engram router
4. Test complex workflows

**Timeline**: 3-4 weeks

### Phase 4: Foundry Tools

**Goal**: Add Foundry Tools for additional capabilities

**Tasks**:
1. Identify useful Foundry Tools
2. Register with agents
3. Integrate tool execution
4. Test new capabilities

**Timeline**: 2-3 weeks

### Phase 5: Microsoft 365 Integration

**Goal**: Publish agents to Teams/Outlook

**Tasks**:
1. Publish Elena to Teams
2. Create Outlook add-in
3. Test integration
4. Document usage

**Timeline**: 3-4 weeks

---

## Feature Comparison Matrix

| Feature | Engram Current | Foundry Alternative | Recommendation |
|---------|---------------|-------------------|----------------|
| **Thread Management** | In-memory | Foundry threads | ✅ Use Foundry |
| **Vector Search** | Zep pgvector | Foundry vectors | ⚠️ Keep Zep (works well) |
| **Multi-Agent** | Custom router | Foundry orchestration | ✅ Use Foundry for complex workflows |
| **Enterprise Search** | Tri-search | Foundry IQ | ✅ Use Foundry IQ for documents |
| **Tools** | Custom LangChain | Foundry Tools | ✅ Use both (hybrid) |
| **Microsoft 365** | Graph API | Foundry integration | ✅ Use Foundry for Teams/Outlook |
| **Fine-Tuning** | None | Foundry fine-tuning | ⚠️ Consider for specialized models |

---

## Recommended Next Steps

### Immediate (This Week)

1. ✅ Complete Elena migration to Foundry
2. ✅ Store Foundry configuration in Key Vault
3. ✅ Test Foundry Elena with Microsoft Graph tools

### Short Term (Next 2-4 Weeks)

1. **Research Foundry IQ**:
   - Evaluate Azure AI Search integration
   - Test with enterprise documents
   - Compare with Engram tri-search

2. **Explore Multi-Agent Orchestration**:
   - Create Foundry workflow
   - Test agent handoffs
   - Compare with Engram router

### Medium Term (Next 1-2 Months)

1. **Foundry Tools Integration**:
   - Identify useful tools
   - Register with agents
   - Test capabilities

2. **Microsoft 365 Integration**:
   - Publish to Teams
   - Create Outlook add-in
   - Test user experience

---

## Summary

**Foundry Features to Leverage**:

1. ✅ **Thread Management** - Already implementing
2. 🎯 **Foundry IQ** - Enterprise document search (high value)
3. 🎯 **Multi-Agent Orchestration** - Complex workflows (high value)
4. 🎯 **Foundry Tools** - Additional capabilities (medium value)
5. 🎯 **Microsoft 365 Integration** - Teams/Outlook (high value)
6. ⚠️ **Vector Stores** - Keep Zep for now (low priority)
7. ⚠️ **Fine-Tuning** - Consider later (low priority)

**Strategy**: **Hybrid Approach**
- Use Foundry for infrastructure and orchestration
- Keep Engram's unique capabilities (tri-search, custom tools)
- Leverage Foundry's strengths (IQ, orchestration, M365 integration)

---

*Last Updated: January 2026*

