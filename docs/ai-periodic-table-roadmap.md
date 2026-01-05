# AI Periodic Table → Engram Architecture Mapping

> **A comprehensive tree-structure mapping of each AI Periodic Table element to Engram's implementation, with a conceptualized roadmap for future development.**

*Baseline: January 5, 2026*

---

## Visual Overview

```
AI PERIODIC TABLE → ENGRAM ARCHITECTURE
═══════════════════════════════════════════════════════════════════════════════

                        ┌─────────────────────────────────────┐
                        │         ENGRAM PLATFORM             │
                        │   Brain (Zep) + Spine (Temporal)    │
                        └───────────────────┬─────────────────┘
                                            │
        ┌───────────────┬───────────────┬───┴───┬───────────────┬───────────────┐
        │               │               │       │               │               │
   ┌────▼────┐    ┌─────▼─────┐   ┌─────▼─────┐ │  ┌───────────▼───────────┐   │
   │ C1      │    │ C2        │   │ C3        │ │  │ C4                    │   │
   │ Reactive│    │ Retrieval │   │ Orchestr. │ │  │ Validation            │   │
   └────┬────┘    └─────┬─────┘   └─────┬─────┘ │  └───────────┬───────────┘   │
        │               │               │       │              │               │
        ▼               ▼               ▼       ▼              ▼               ▼
   ┌─────────┐    ┌─────────┐    ┌──────────┐ ┌─────────┐ ┌─────────┐    ┌─────────┐
   │Pr Em Fc │    │Vx Ft Sy │    │Rg Fw Gk  │ │Gr Rt In │ │Lg Mm Sm │    │   Th    │
   │Ag Ma    │    │         │    │          │ │         │ │         │    │         │
   └─────────┘    └─────────┘    └──────────┘ └─────────┘ └─────────┘    └─────────┘
```

---

## Element-by-Element Tree Mapping

### 🟢 ROW 1: PRIMITIVES (Foundation Layer)

```
R1 PRIMITIVES
├── Pr (Prompts) ──────────────────────────────────── 🟢 STRONG
│   ├── Current Implementation
│   │   ├── backend/agents/elena/agent.py → ElenaAgent.system_prompt
│   │   ├── backend/agents/marcus/agent.py → MarcusAgent.system_prompt
│   │   ├── backend/agents/sage/agent.py → SageAgent.system_prompt
│   │   └── backend/llm/claude_client.py → SAGE_SYSTEM_PROMPT
│   │
│   ├── Key Features
│   │   ├── Context-First Requirements Framework (Elena)
│   │   ├── Calm in the Storm Leadership (Marcus)
│   │   ├── Sage Meridian Storyteller persona
│   │   └── Enterprise context injection via EnterpriseContext.to_llm_context()
│   │
│   └── Roadmap
│       ├── [ ] Prompt versioning and A/B testing
│       ├── [ ] Dynamic prompt composition based on user role
│       └── [ ] Prompt performance analytics dashboard
│
├── Em (Embeddings) ───────────────────────────────── 🟢 STRONG
│   ├── Current Implementation
│   │   ├── Zep Cloud → Automatic embedding on message ingestion
│   │   ├── backend/memory/client.py → search_memory()
│   │   └── backend/etl/ingestion_service.py → Document chunking + embedding
│   │
│   ├── Key Features
│   │   ├── Tri-Search (Keyword + Vector + Graph)
│   │   ├── Automatic entity extraction
│   │   └── Cross-session knowledge compounding
│   │
│   └── Roadmap
│       ├── [ ] Custom embedding models for domain-specific terms
│       ├── [ ] Embedding drift detection
│       └── [ ] Multi-modal embeddings (text + image)
│
└── Lg (LLM) ──────────────────────────────────────── 🟢 STRONG
    ├── Current Implementation
    │   ├── backend/agents/base.py → FoundryChatClient
    │   ├── backend/llm/claude_client.py → ClaudeClient (Anthropic)
    │   ├── backend/llm/gemini_client.py → GeminiClient (Google)
    │   └── Azure APIM Gateway → Model Router pattern
    │
    ├── Key Features
    │   ├── Multi-model orchestration (Claude for text, Gemini for visuals)
    │   ├── Automatic fallback (Anthropic API → Azure APIM)
    │   ├── Model Router for dynamic model selection
    │   └── Token-based authentication (Azure AD + API keys)
    │
    └── Roadmap
        ├── [ ] Cost-aware model routing (use cheaper models for simple tasks)
        ├── [ ] Latency-optimized routing (edge deployment)
        └── [ ] Model performance comparison dashboard
```

---

### 🟢 ROW 2: COMPOSITIONS (Integration Layer)

```
R2 COMPOSITIONS
├── Fc (Function Call) ────────────────────────────── 🟢 STRONG
│   ├── Current Implementation
│   │   ├── backend/agents/github_tools.py
│   │   │   ├── create_github_issue_tool
│   │   │   ├── update_github_issue_tool
│   │   │   ├── get_project_status_tool
│   │   │   ├── list_my_tasks_tool
│   │   │   └── close_task_tool
│   │   │
│   │   ├── backend/agents/elena/agent.py
│   │   │   ├── search_memory_tool
│   │   │   ├── send_email_tool (Microsoft Graph)
│   │   │   ├── list_onedrive_files_tool
│   │   │   ├── save_to_onedrive_tool
│   │   │   ├── trigger_ingestion_tool
│   │   │   ├── run_golden_thread_tool
│   │   │   ├── analyze_requirements
│   │   │   ├── stakeholder_mapping
│   │   │   ├── create_user_story
│   │   │   └── delegate_to_sage
│   │   │
│   │   ├── backend/agents/marcus/agent.py
│   │   │   ├── create_project_timeline
│   │   │   ├── assess_project_risks
│   │   │   ├── create_status_report
│   │   │   ├── estimate_effort
│   │   │   ├── delegate_to_sage
│   │   │   ├── start_bau_flow_tool
│   │   │   └── check_workflow_status_tool
│   │   │
│   │   └── backend/agents/sage/agent.py
│   │       ├── generate_story
│   │       ├── generate_diagram
│   │       └── generate_visual
│   │
│   ├── Key Features
│   │   ├── LangChain @tool decorator pattern
│   │   ├── Async tool execution
│   │   ├── Tool result injection into state
│   │   └── Cross-agent delegation (Elena → Sage, Marcus → Sage)
│   │
│   └── Roadmap
│       ├── [ ] MCP (Model Context Protocol) server implementation
│       ├── [ ] Tool discovery and dynamic registration
│       ├── [ ] Tool execution analytics and cost tracking
│       └── [ ] Sandboxed tool execution for untrusted tools
│
├── Vx (Vector) ───────────────────────────────────── 🟢 STRONG
│   ├── Current Implementation
│   │   ├── Zep Cloud → Built-in vector store
│   │   ├── backend/memory/client.py → ZepMemoryClient
│   │   └── Tri-Search combines vector with keyword and graph
│   │
│   ├── Key Features
│   │   ├── Automatic vectorization on ingestion
│   │   ├── Semantic similarity search
│   │   ├── Configurable top-k retrieval
│   │   └── Confidence scores on results
│   │
│   └── Roadmap
│       ├── [ ] Hybrid vector stores (Zep + Pinecone for scale)
│       ├── [ ] Vector index optimization for large corpora
│       └── [ ] Real-time vector updates (streaming ingestion)
│
├── Rg (RAG) ──────────────────────────────────────── 🟢 STRONG
│   ├── Current Implementation
│   │   ├── backend/agents/base.py → _reason_node() → Automatic RAG
│   │   ├── backend/memory/client.py → search_memory()
│   │   └── backend/workflows/story_activities.py → Tri-Search Verification
│   │
│   ├── Key Features
│   │   ├── Automatic context injection in every agent turn
│   │   ├── Memory retrieval with relevance scoring
│   │   ├── Cross-session knowledge assembly
│   │   └── "Double Tri-Search Verification" pattern for Sage
│   │
│   └── Roadmap
│       ├── [ ] Agentic RAG (agent decides what to retrieve)
│       ├── [ ] Multi-hop reasoning over retrieved context
│       ├── [ ] Source attribution and citation
│       └── [ ] Retrieval quality metrics dashboard
│
├── Gr (Guardrails) ───────────────────────────────── 🟢 STRONG
│   ├── Current Implementation
│   │   ├── backend/auth/middleware.py → Azure Entra ID integration
│   │   ├── backend/core/security.py → SecurityContext, RBAC
│   │   ├── Azure Container Apps → Network isolation
│   │   └── Azure CIAM → External identity management
│   │
│   ├── Key Features
│   │   ├── JWT token validation
│   │   ├── Role-based access control (Admin, User, Guest)
│   │   ├── Tenant isolation
│   │   └── API rate limiting
│   │
│   └── Roadmap
│       ├── [ ] Content moderation (Azure Content Safety)
│       ├── [ ] PII detection and redaction
│       ├── [ ] Output validation against schemas
│       └── [ ] Compliance logging (SOC2, HIPAA)
│
└── Mm (Multimodal) ───────────────────────────────── 🟢 STRONG
    ├── Current Implementation
    │   ├── backend/llm/gemini_client.py → generate_image_from_spec()
    │   │   └── Uses Imagen 3.0 (Nano Banana Pro)
    │   ├── backend/api/routers/voice.py → VoiceLive integration
    │   │   └── Azure AI Voice (real-time speech)
    │   └── backend/workflows/story_activities.py → Image generation pipeline
    │
    ├── Key Features
    │   ├── Text → Image generation (Gemini/Imagen)
    │   ├── Voice → Text → Voice (VoiceLive)
    │   ├── Diagram spec → Visual rendering
    │   └── Story + Image + Diagram bundling
    │
    └── Roadmap
        ├── [ ] Image → Text understanding (vision models)
        ├── [ ] Video generation (Veo)
        ├── [ ] Document understanding (PDF → structured data)
        └── [ ] Multi-modal memory (store and retrieve images)
```

---

### 🟡 ROW 3: DEPLOYMENT (Production Layer)

```
R3 DEPLOYMENT
├── Ag (Agent) ────────────────────────────────────── 🟢 STRONG
│   ├── Current Implementation
│   │   ├── backend/agents/elena/ → Dr. Elena Vasquez (Business Analyst)
│   │   ├── backend/agents/marcus/ → Marcus Chen (Project Manager)
│   │   ├── backend/agents/sage/ → Sage Meridian (Storyteller)
│   │   └── backend/agents/base.py → BaseAgent (LangGraph foundation)
│   │
│   ├── Key Features
│   │   ├── Persona-based system prompts
│   │   ├── Tool-augmented reasoning
│   │   ├── State machine (LangGraph StateGraph)
│   │   └── Memory-enriched context (RAG pattern)
│   │
│   └── Roadmap
│       ├── [ ] Agent templating system (create new agents easily)
│       ├── [ ] Agent performance benchmarking
│       ├── [ ] Agent marketplace (share/import agent definitions)
│       └── [ ] Self-improving agents (learn from feedback)
│
├── Ft (Finetune) ─────────────────────────────────── 🔴 GAP (Issue #9)
│   ├── Current Implementation
│   │   └── (Not implemented)
│   │
│   ├── Conceptualized Roadmap
│   │   ├── Phase 1: Data Collection
│   │   │   ├── [ ] Capture high-quality conversation pairs from Zep
│   │   │   ├── [ ] Export successful tool invocations as training data
│   │   │   └── [ ] Curate domain-specific Q&A from episodes
│   │   │
│   │   ├── Phase 2: Fine-tuning Infrastructure
│   │   │   ├── [ ] Azure AI Fine-tuning service integration
│   │   │   ├── [ ] Granite/Llama fine-tuning on Azure ML
│   │   │   └── [ ] LoRA adapters for cost-effective customization
│   │   │
│   │   └── Phase 3: Deployment
│   │       ├── [ ] A/B testing fine-tuned vs base models
│   │       ├── [ ] Domain-specific models (legal, medical, finance)
│   │       └── [ ] Customer-specific model customization service
│
├── Fw (Framework) ────────────────────────────────── 🟢 STRONG
│   ├── Current Implementation
│   │   ├── Temporal Server → Durable workflow orchestration
│   │   ├── backend/workflows/story_workflow.py → StoryWorkflow
│   │   ├── backend/workflows/story_activities.py → Activity definitions
│   │   ├── backend/workflows/client.py → Workflow client
│   │   └── LangGraph → Agent state machines
│   │
│   ├── Key Features
│   │   ├── Durable execution (survives restarts)
│   │   ├── Retry policies with exponential backoff
│   │   ├── Observable via Temporal UI
│   │   ├── Activity-based decomposition
│   │   └── Cross-service orchestration
│   │
│   └── Roadmap
│       ├── [ ] Workflow versioning and migration
│       ├── [ ] Long-running autonomous workflows (days/weeks)
│       ├── [ ] Human-in-the-loop approval steps
│       └── [ ] Workflow analytics and optimization
│
├── Rt (Red-team) ─────────────────────────────────── 🟡 EMERGING (Issue #12)
│   ├── Current Implementation
│   │   ├── backend/validation/validation_service.py → Basic validation
│   │   └── Golden Thread verification (deterministic checks)
│   │
│   ├── Key Features (Partial)
│   │   ├── JSON schema validation
│   │   ├── Required field checking
│   │   └── Format validation
│   │
│   └── Conceptualized Roadmap
│       ├── Phase 1: Automated Testing
│       │   ├── [ ] Prompt injection detection
│       │   ├── [ ] Jailbreak attempt monitoring
│       │   └── [ ] Output toxicity scanning
│       │
│       ├── Phase 2: Adversarial Probing
│       │   ├── [ ] Automated red-team agent
│       │   ├── [ ] Boundary testing for guardrails
│       │   └── [ ] Hallucination detection
│       │
│       └── Phase 3: Continuous Monitoring
│           ├── [ ] Production anomaly detection
│           ├── [ ] User feedback loop for safety issues
│           └── [ ] Incident response playbook
│
└── Sm (Small Models) ─────────────────────────────── 🔴 GAP (Issue #10)
    ├── Current Implementation
    │   └── (Not implemented - all models are large/cloud-based)
    │
    └── Conceptualized Roadmap
        ├── Phase 1: Evaluation
        │   ├── [ ] Benchmark Phi-4, Granite, Gemma 2B on Engram tasks
        │   ├── [ ] Identify tasks suitable for small models
        │   │   ├── Classification (route to agent)
        │   │   ├── Entity extraction
        │   │   ├── Summarization
        │   │   └── JSON parsing
        │   └── [ ] Cost-benefit analysis vs large models
        │
        ├── Phase 2: Integration
        │   ├── [ ] Azure ML endpoint for small models
        │   ├── [ ] Model Router aware of small model options
        │   └── [ ] Fallback to large model on low confidence
        │
        └── Phase 3: Edge Deployment
            ├── [ ] ONNX export for client-side inference
            ├── [ ] Mobile SDK with embedded model
            └── [ ] Offline-first capabilities
```

---

### ⭐ ROW 4: EMERGING (Innovation Layer)

```
R4 EMERGING
├── Ma (Multi-agent) ──────────────────────────────── 🟢 STRONG
│   ├── Current Implementation
│   │   ├── backend/agents/router.py → Agent routing logic
│   │   ├── Elena.delegate_to_sage() → Temporal workflow delegation
│   │   ├── Marcus.delegate_to_sage() → Same pattern
│   │   └── backend/workflows/client.py → execute_story()
│   │
│   ├── Key Features
│   │   ├── Agent-to-agent delegation via Temporal
│   │   ├── Durable handoff (survives failures)
│   │   ├── Workflow-based coordination
│   │   └── Result aggregation
│   │
│   └── Roadmap
│       ├── [ ] Agent negotiation protocols
│       ├── [ ] Parallel agent execution (divide and conquer)
│       ├── [ ] Agent coordination via shared memory (Zep)
│       ├── [ ] Supervisor agent pattern
│       └── [ ] Agent swarm for complex research tasks
│
├── Sy (Synthetic) ────────────────────────────────── 🟢 STRONG
│   ├── Current Implementation
│   │   ├── backend/workflows/story_workflow.py → StoryWorkflow
│   │   ├── backend/llm/claude_client.py → generate_story()
│   │   ├── backend/llm/gemini_client.py → generate_visual_spec(), generate_image()
│   │   └── backend/workflows/story_activities.py → Full pipeline
│   │
│   ├── Key Features
│   │   ├── Story generation with Claude
│   │   ├── Diagram spec generation with Gemini
│   │   ├── Image generation with Imagen 3.0
│   │   ├── Artifact persistence to OneDrive/Azure File Share
│   │   └── Memory enrichment (stories become searchable knowledge)
│   │
│   └── Roadmap
│       ├── [ ] Synthetic data generation for training
│       ├── [ ] Auto-documentation from code
│       ├── [ ] Meeting summary generation
│       ├── [ ] Report generation from structured data
│       └── [ ] Presentation slide generation
│
├── Gk (Graph Knowledge) ──────────────────────────── ⭐ UNIQUE DIFFERENTIATOR
│   ├── Current Implementation
│   │   ├── Zep Cloud → Temporal Knowledge Graph
│   │   ├── backend/memory/client.py → ZepMemoryClient
│   │   │   ├── get_entities()
│   │   │   ├── get_facts()
│   │   │   └── search_memory() → Tri-Search
│   │   └── Automatic entity/relationship extraction
│   │
│   ├── Key Features
│   │   ├── Entities: People, projects, concepts extracted automatically
│   │   ├── Facts: Relationships between entities with timestamps
│   │   ├── Temporal awareness: Knowledge evolves over time
│   │   ├── Cross-session learning: Agents remember across conversations
│   │   └── Graph traversal for context assembly
│   │
│   ├── Why This Is Unique
│   │   ├── Most platforms use static RAG (Rg)
│   │   ├── Gk enables DYNAMIC context orchestration
│   │   ├── Knowledge compounds automatically
│   │   └── Semantic routing based on relationships
│   │
│   └── Roadmap
│       ├── [ ] Graph visualization in UI (network diagram)
│       ├── [ ] Manual entity/fact curation interface
│       ├── [ ] Graph-based recommendations
│       ├── [ ] Federated graphs (cross-tenant knowledge sharing)
│       └── [ ] Causal reasoning over graph
│
├── In (Interpret) ────────────────────────────────── 🔴 GAP (Issue #11)
│   ├── Current Implementation
│   │   └── (Not implemented)
│   │
│   └── Conceptualized Roadmap
│       ├── Phase 1: Transparency
│       │   ├── [ ] Tool invocation logging with explanations
│       │   ├── [ ] "Why did you say that?" feature
│       │   └── [ ] Memory retrieval visualization
│       │
│       ├── Phase 2: Explainability
│       │   ├── [ ] Attention visualization
│       │   ├── [ ] Confidence scores on outputs
│       │   ├── [ ] Alternative response suggestions
│       │   └── [ ] Source attribution (which memory informed this?)
│       │
│       └── Phase 3: Auditability
│           ├── [ ] Full decision trace export
│           ├── [ ] Compliance reporting (why this recommendation?)
│           ├── [ ] Bias detection and reporting
│           └── [ ] Regulatory submission formatting
│
└── Th (Thinking) ─────────────────────────────────── 🟢 STRONG
    ├── Current Implementation
    │   ├── LangGraph StateGraph → Multi-step reasoning
    │   ├── backend/agents/base.py → _reason_node()
    │   ├── Tool results → Injected into next reasoning step
    │   └── Memory → Context-enriched reasoning
    │
    ├── Key Features
    │   ├── State machine-based reasoning
    │   ├── Conditional branching (should_continue)
    │   ├── Tool-augmented thinking
    │   └── Memory-enriched context
    │
    └── Roadmap
        ├── [ ] Chain-of-thought prompting (explicit reasoning steps)
        ├── [ ] Tree-of-thought (parallel reasoning branches)
        ├── [ ] Self-reflection (evaluate own outputs)
        ├── [ ] Planning (decompose complex tasks)
        └── [ ] Metacognition (agent awareness of own limitations)
```

---

## Summary Statistics

| Status | Count | Elements |
|--------|-------|----------|
| 🟢 Strong | 12 | Pr, Em, Lg, Fc, Vx, Rg, Gr, Mm, Ag, Fw, Ma, Sy, Th |
| 🟡 Emerging | 1 | Rt |
| 🔴 Gap | 3 | Ft, Sm, In |
| ⭐ Unique | 1 | Gk |

---

## Roadmap Priority Matrix

```
                        IMPACT
                    Low         High
                ┌──────────┬──────────┐
        Low     │          │    Sm    │
    EFFORT      │          │ (edge)   │
                ├──────────┼──────────┤
        High    │    Ft    │  In, Rt  │
                │(finetune)│(regulate)│
                └──────────┴──────────┘
```

### Recommended Implementation Order

1. **In (Interpret)** - High impact for compliance, moderate effort
2. **Rt (Red-team)** - Critical for production safety
3. **Sm (Small Models)** - Cost optimization, edge deployment
4. **Ft (Finetune)** - Domain customization, requires data

---

## Related Documents

- [Business Plan](../business-plan-ai-periodic-table.md)
- [Interactive Matrix](../ai-periodic-table-matrix.html)
- [Wiki Overview](../wiki/ai-periodic-table.md)
- [Baseline Milestone](../milestones/2026-01-05-ai-periodic-table-baseline.md)

---

*Framework credit: [Martin Keen](https://www.linkedin.com/in/martingkeen/), IBM Master Inventor | [Video](https://youtu.be/ESBMgZHzfG0?si=Q2GME-RqGHjGaz_6)*
