# Engram AI Periodic Table Business Plan

> **Elena Rivera's strategic mapping of Engram capabilities to Martin Keen's AI Periodic Table, demonstrating competitive strength in each element.**

---

## Executive Summary

Martin Keen's AI Periodic Table provides a framework for understanding the building blocks of modern AI systems. This business plan maps Engram's architecture to each element, identifying:

- **Strong**: Production-ready implementation
- **Emerging**: Partially implemented, roadmap priority
- **Gap**: Not yet addressed, opportunity for development

**Key Finding**: Engram demonstrates **Strong** implementation in 12 of 18 elements, with our proposed **Gk (Graph Knowledge)** element representing a unique competitive advantage.

---

## The AI Periodic Table Structure

### Rows (Maturity Levels)

| Row | Name | Description |
|-----|------|-------------|
| R1 | **Primitives** | Foundational building blocks |
| R2 | **Compositions** | Combined capabilities |
| R3 | **Deployment** | Production patterns |
| R4 | **Emerging** | Cutting-edge innovations |

### Columns (Capability Domains)

| Column | Name | Description |
|--------|------|-------------|
| C1 | **Reactive** | Response to stimuli |
| C2 | **Retrieval** | Information access |
| C3 | **Orchestration** | Workflow coordination |
| C4 | **Validation** | Quality assurance |
| C5 | **Models** | AI model types |

---

## Element-by-Element Analysis

### Row 1: Primitives

#### Pr (Prompts) — C1 Reactive × R1 Primitives

**Status**: 🟢 **Strong**

| Aspect | Engram Implementation |
|--------|----------------------|
| **Component** | Agent system prompts |
| **Location** | `backend/agents/{elena,marcus,sage}.py` |
| **Strength** | Three distinct agent personalities with rich, contextual system prompts |
| **Differentiation** | Prompts are not static—they incorporate tri-search context dynamically |

**Business Value**: Engram's prompts define personality, not just function. Elena, Marcus, and Sage each have distinct voices, expertise areas, and behavioral patterns that create a memorable user experience.

---

#### Em (Embeddings) — C2 Retrieval × R1 Primitives

**Status**: 🟢 **Strong**

| Aspect | Engram Implementation |
|--------|----------------------|
| **Component** | Zep embedding layer |
| **Location** | `backend/memory/client.py` |
| **Strength** | Automatic embedding of all conversations and artifacts |
| **Model** | OpenAI ada-002 via Zep Cloud |

**Business Value**: Every interaction is automatically embedded and searchable. No manual indexing required—memory builds organically through use.

---

#### Lg (LLM) — C5 Models × R1 Primitives

**Status**: 🟢 **Strong**

| Aspect | Engram Implementation |
|--------|----------------------|
| **Component** | Multi-model orchestration |
| **Location** | `backend/llm/{claude,gemini}_client.py`, model router |
| **Strength** | Claude Sonnet 4, Gemini 2.0 Flash, GPT-4o, with automatic fallback |
| **Architecture** | Model router selects optimal model per query type |

**Business Value**: Not locked to a single vendor. Engram uses the best model for each task while maintaining resilience through fallback chains.

---

### Row 2: Compositions

#### Fc (Function Call) — C1 Reactive × R2 Compositions

**Status**: 🟢 **Strong**

| Aspect | Engram Implementation |
|--------|----------------------|
| **Component** | MCP (Model Context Protocol) Tools |
| **Location** | `backend/api/routers/mcp.py`, `mcp_server.py` |
| **Strength** | 40+ tools including memory, search, delegation, schema management |
| **Protocol** | MCP-compatible, works with Claude Desktop and other MCP clients |

**Business Value**: Engram agents can take action, not just answer questions. They query databases, create stories, search memory, and delegate tasks.

---

#### Vx (Vector) — C2 Retrieval × R2 Compositions

**Status**: 🟢 **Strong**

| Aspect | Engram Implementation |
|--------|----------------------|
| **Component** | Zep vector store |
| **Location** | Memory client semantic search |
| **Strength** | Tri-Search: semantic (vector) + keyword + graph combined |
| **Scale** | Cloud-hosted, handles millions of embeddings |

**Business Value**: Tri-Search surpasses traditional RAG by combining three retrieval methods. Users get better context without knowing how search works.

---

#### Rg (RAG) — C3 Orchestration × R2 Compositions

**Status**: 🟢 **Strong**

| Aspect | Engram Implementation |
|--------|----------------------|
| **Component** | Context assembly pipeline |
| **Location** | `backend/agents/base.py`, memory enrichment |
| **Strength** | Automatic retrieval-augmented generation on every query |
| **Architecture** | Search → Filter → Inject → Generate → Store |

**Business Value**: Every agent response is grounded in memory. Hallucinations reduced through automatic context injection.

---

#### Gr (Guardrails) — C4 Validation × R2 Compositions

**Status**: 🟢 **Strong**

| Aspect | Engram Implementation |
|--------|----------------------|
| **Component** | Enterprise security middleware |
| **Location** | `backend/api/middleware/auth.py` |
| **Strength** | Azure Entra ID integration, tenant isolation, RBAC |
| **Compliance** | Enterprise-ready authentication for all endpoints |

**Business Value**: Not a toy—Engram is built for enterprise from day one. Multi-tenant isolation ensures customer data sovereignty.

---

#### Mm (Multimodal) — C5 Models × R2 Compositions

**Status**: 🟢 **Strong**

| Aspect | Engram Implementation |
|--------|----------------------|
| **Component** | Image + Voice + Text |
| **Location** | `gemini_client.py` (Imagen 3.0), `voice.py` (VoiceLive) |
| **Strength** | Story visuals via Imagen, real-time voice via Azure VoiceLive |
| **Architecture** | Two-step image generation: spec → image |

**Business Value**: Engram creates, not just answers. Stories include visuals. Voice enables hands-free interaction.

---

### Row 3: Deployment

#### Ag (Agent) — C1 Reactive × R3 Deployment

**Status**: 🟢 **Strong**

| Aspect | Engram Implementation |
|--------|----------------------|
| **Component** | Elena, Marcus, Sage |
| **Location** | `backend/agents/` |
| **Strength** | Three production agents with distinct capabilities |
| **Specialization** | Elena (orchestrator), Marcus (engineer), Sage (storyteller) |

**Business Value**: Specialized agents outperform generalist chatbots. Users get expert assistance matched to their need.

---

#### Ft (Finetune) — C2 Retrieval × R3 Deployment

**Status**: 🟡 **Gap**

| Aspect | Status |
|--------|--------|
| **Current** | Not implemented |
| **Roadmap** | Custom fine-tuned models for domain-specific tasks |
| **Opportunity** | Fine-tune Granite or Llama for Engram-specific patterns |

**Business Value**: Future opportunity for specialized, lower-cost inference on common tasks.

---

#### Fw (Framework) — C3 Orchestration × R3 Deployment

**Status**: 🟢 **Strong**

| Aspect | Engram Implementation |
|--------|----------------------|
| **Component** | Temporal workflows |
| **Location** | `backend/workflows/` |
| **Strength** | Durable execution for multi-step agent tasks |
| **Architecture** | Story, agent, conversation workflows with retry policies |

**Business Value**: Engram doesn't fail silently. Long-running tasks survive outages and can be monitored in real-time.

---

#### Rt (Red-team) — C4 Validation × R3 Deployment

**Status**: 🟡 **Emerging**

| Aspect | Status |
|--------|--------|
| **Current** | Basic input validation |
| **Roadmap** | Adversarial testing, prompt injection detection |
| **Opportunity** | Integration with Azure AI Content Safety |

**Business Value**: Critical for enterprise trust. Roadmap item for security-conscious customers.

---

#### Sm (Small) — C5 Models × R3 Deployment

**Status**: 🟡 **Gap**

| Aspect | Status |
|--------|--------|
| **Current** | Not implemented |
| **Roadmap** | IBM Granite 3.3, Microsoft Phi-4 for edge deployment |
| **Opportunity** | Lower costs, faster inference, on-premises option |

**Business Value**: Small models enable cost-effective high-volume scenarios and edge deployment without cloud dependency.

---

### Row 4: Emerging

#### Ma (Multi-agent) — C1 Reactive × R4 Emerging

**Status**: 🟢 **Strong**

| Aspect | Engram Implementation |
|--------|----------------------|
| **Component** | Agent delegation |
| **Location** | `backend/agents/delegation.py` |
| **Strength** | Elena delegates to Sage for stories, to Marcus for technical tasks |
| **Architecture** | Delegation via MCP tools, results flow back to originator |

**Business Value**: Complex tasks are automatically routed to specialists. Users don't need to know which agent to ask.

---

#### Sy (Synthetic) — C2 Retrieval × R4 Emerging

**Status**: 🟢 **Strong**

| Aspect | Engram Implementation |
|--------|----------------------|
| **Component** | Story + visual generation |
| **Location** | `story_workflow.py`, `story_activities.py` |
| **Strength** | Claude generates narratives, Gemini generates visuals |
| **Output** | Markdown stories with embedded architecture diagrams and images |

**Business Value**: Engram creates knowledge, not just retrieves it. Technical concepts become memorable stories with visuals.

---

#### Gk (Graph Knowledge) — C3 Orchestration × R4 Emerging

**Status**: 🟢 **UNIQUE STRENGTH** ⭐

| Aspect | Engram Implementation |
|--------|----------------------|
| **Component** | Zep temporal knowledge graph |
| **Location** | `backend/memory/client.py`, Zep Cloud integration |
| **Strength** | Entity extraction, fact linking, temporal awareness |
| **Architecture** | Knowledge compounds across sessions automatically |

**Capabilities**:

1. **Entity Extraction**: People, systems, concepts extracted from every conversation
2. **Fact Linking**: Relationships stored as graph edges with timestamps
3. **Temporal Queries**: "What did Derek know about HorizonDB last week?"
4. **Cross-Session Learning**: Knowledge persists and grows without explicit ingestion

**Why This Is Our Moat**:
> While competitors use static RAG (retrieve → augment → generate), Engram uses **dynamic Graph Knowledge orchestration**. Context assembly is driven by semantic understanding of entity relationships, not just vector similarity.

**Business Value**: Engram remembers relationships, not just facts. This enables true continuity across conversations and compound learning over time.

---

#### In (Interpret) — C4 Validation × R4 Emerging

**Status**: 🟡 **Gap**

| Aspect | Status |
|--------|--------|
| **Current** | Not implemented |
| **Roadmap** | Explainability for agent decisions |
| **Opportunity** | "Why did Elena suggest this?" transparency |

**Business Value**: Critical for regulated industries. Enables audit trails for AI-assisted decisions.

---

#### Th (Thinking) — C5 Models × R4 Emerging

**Status**: 🟢 **Strong**

| Aspect | Engram Implementation |
|--------|----------------------|
| **Component** | Extended thinking in workflows |
| **Location** | Temporal activity design |
| **Strength** | Multi-step reasoning with query handlers for progress |
| **Architecture** | Workflows support long-running "thinking" tasks |

**Business Value**: Complex reasoning isn't rushed. Story generation takes 2-3 minutes because quality matters more than speed.

---

## Competitive Position Summary

| Status | Count | Elements |
|--------|-------|----------|
| 🟢 **Strong** | 12 | Pr, Em, Lg, Fc, Vx, Rg, Gr, Mm, Ag, Fw, Ma, Sy, Gk, Th |
| 🟡 **Emerging/Gap** | 4 | Ft, Rt, Sm, In |

### Unique Differentiator: Gk (Graph Knowledge)

Engram is the **only** platform with production-ready Graph Knowledge implementation. While:

- OpenAI offers GPT-4 (Lg) and function calling (Fc)
- Anthropic offers Claude (Lg) and thinking (Th)
- Microsoft offers Azure AI (Lg) with guardrails (Gr)

**Only Engram combines all of these with temporal knowledge graphs that enable true context engineering.**

---

## Roadmap Priorities

1. **Sm (Small Models)**: Deploy Phi-4 or Granite for high-volume edge scenarios
2. **In (Interpret)**: Build explainability layer for enterprise compliance
3. **Rt (Red-team)**: Integrate adversarial testing for security assurance
4. **Ft (Finetune)**: Custom models for domain-specific tasks

---

## Visual: Engram on the AI Periodic Table

```
     C1 Reactive   C2 Retrieval   C3 Orchestration   C4 Validation   C5 Models
   ┌──────────────┬──────────────┬──────────────────┬───────────────┬──────────────┐
R1 │   🟢 Pr      │   🟢 Em      │                  │               │   🟢 Lg      │
   │   Prompts    │  Embeddings  │                  │               │    LLM       │
   ├──────────────┼──────────────┼──────────────────┼───────────────┼──────────────┤
R2 │   🟢 Fc      │   🟢 Vx      │     🟢 Rg        │    🟢 Gr      │   🟢 Mm      │
   │ Function Call│   Vector     │      RAG         │  Guardrails   │  Multimodal  │
   ├──────────────┼──────────────┼──────────────────┼───────────────┼──────────────┤
R3 │   🟢 Ag      │   🟡 Ft      │     🟢 Fw        │    🟡 Rt      │   🟡 Sm      │
   │    Agent     │  Finetune    │   Framework      │  Red-team     │    Small     │
   ├──────────────┼──────────────┼──────────────────┼───────────────┼──────────────┤
R4 │   🟢 Ma      │   🟢 Sy      │     ⭐ Gk        │    🟡 In      │   🟢 Th      │
   │ Multi-agent  │  Synthetic   │ Graph Knowledge  │  Interpret    │  Thinking    │
   └──────────────┴──────────────┴──────────────────┴───────────────┴──────────────┘

🟢 = Strong    🟡 = Gap/Emerging    ⭐ = Unique Differentiator
```

---

*This business plan was prepared by Elena Rivera, Chief Strategy Officer for Engram.*
