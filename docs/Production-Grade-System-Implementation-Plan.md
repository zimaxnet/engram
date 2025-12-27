# Production-Grade Agentic System Implementation Plan

## Executive Summary

This document provides a comprehensive work breakdown structure (WBS) for implementing all **Seven Layers of Production-Grade Agentic Systems** in Engram. Based on the maturity assessment (current: ⭐⭐⭐☆☆ 3.0/5.0), this plan prioritizes critical gaps and provides actionable tasks with dependencies.

**Target Maturity: ⭐⭐⭐⭐⭐ (5.0/5.0)**

---

## Current State Summary

| Layer | Current Rating | Target Rating | Priority | Estimated Effort |
|-------|---------------|---------------|----------|------------------|
| Layer 1: Interaction | ⭐⭐⭐☆☆ (3.0) | ⭐⭐⭐⭐⭐ (5.0) | High | 4 weeks |
| Layer 2: Orchestration | ⭐⭐⭐⭐☆ (3.75) | ⭐⭐⭐⭐⭐ (5.0) | Medium | 3 weeks |
| Layer 3: Cognition | ⭐⭐⭐☆☆ (2.67) | ⭐⭐⭐⭐⭐ (5.0) | High | 4 weeks |
| Layer 4: Memory | ⭐⭐⭐☆☆ (3.33) | ⭐⭐⭐⭐⭐ (5.0) | Medium | 3 weeks |
| Layer 5: Tools | ⭐⭐⭐☆☆ (3.0) | ⭐⭐⭐⭐⭐ (5.0) | Medium | 3 weeks |
| Layer 6: Guardrails | ⭐☆☆☆☆ (0.8) | ⭐⭐⭐⭐⭐ (5.0) | **CRITICAL** | 4 weeks |
| Layer 7: Observability | ⭐⭐⭐☆☆ (3.0) | ⭐⭐⭐⭐⭐ (5.0) | High | 3 weeks |

**Total Estimated Effort: 24 weeks (6 months)**

---

## Agent Integration with GitHub Projects

**Elena and Marcus are authorized to interact with GitHub Projects** to track implementation progress. Both agents have access to:

- ✅ Create GitHub issues for tasks
- ✅ Update issue status and progress
- ✅ Query project status and metrics
- ✅ List assigned tasks
- ✅ Close completed tasks

**Authorization:** Agents use a GitHub Personal Access Token (configured via `GITHUB_TOKEN` environment variable) with `repo`, `read:project`, and `write:project` scopes.

**System Awareness:** The Engram system is aware of GitHub Projects progress through:
- Agent queries to `get_project_status` tool
- Automatic issue creation for new tasks
- Progress tracking via issue state (open/closed)
- Status reports generated from GitHub data

See `docs/GitHub-Integration-Authorization.md` for detailed setup and authorization model.

---

## Phase 1: Critical Security & Safety (Weeks 1-4)

### 🚨 Layer 6: Guardrails - CRITICAL PRIORITY

**Current State:** ⭐☆☆☆☆ (0.8/5.0) - **MUST FIX BEFORE PRODUCTION**

#### Task 6.1: Input Guardrails Implementation
**Priority:** Critical | **Effort:** 1.5 weeks | **Dependencies:** None | **Owner:** Elena (Business Analyst) | **Reviewer:** Marcus (Project Manager) | **Owner:** Elena (Business Analyst) | **Reviewer:** Marcus (Project Manager)

**Sub-tasks:**
- [ ] **6.1.1** Create `backend/guardrails/input_guard.py` module
  - [ ] Implement prompt injection detection using Rebuff or Microsoft Presidio
  - [ ] Add jailbreak pattern detection (DAN mode, role-playing, etc.)
  - [ ] Create `detect_prompt_injection(text: str) -> bool` function
  - [ ] Add logging for all filtered inputs (audit trail)

- [ ] **6.1.2** PII Redaction Middleware
  - [ ] Integrate Microsoft Presidio or similar PII detection library
  - [ ] Create `redact_pii(text: str) -> str` function
  - [ ] Support: SSN, credit cards, email addresses, IP addresses, phone numbers
  - [ ] Add configuration for custom PII patterns (internal IDs, etc.)

- [ ] **6.1.3** Input Validation Pipeline
  - [ ] Create `InputGuardrails` class with `validate_input(text: str) -> GuardResult`
  - [ ] Integrate into FastAPI middleware (`backend/api/middleware/guardrails.py`)
  - [ ] Apply to all `/api/v1/chat/*` and `/api/v1/agents/*` endpoints
  - [ ] Return structured errors (don't expose detection patterns)

**Acceptance Criteria:**
- All user inputs pass through guardrails before reaching LLM
- Prompt injection attempts are detected and logged
- PII is automatically redacted before LLM calls
- Audit log contains all filtered inputs with timestamps

**Files to Create/Modify:**
- `backend/guardrails/__init__.py` (new)
- `backend/guardrails/input_guard.py` (new)
- `backend/api/middleware/guardrails.py` (new)
- `backend/api/routers/chat.py` (modify - add middleware)
- `backend/api/routers/agents.py` (modify - add middleware)

---

#### Task 6.2: Execution Guardrails
**Priority:** High | **Effort:** 1 week | **Dependencies:** 6.1 | **Owner:** Marcus (Project Manager) | **Reviewer:** Elena (Business Analyst) | **Owner:** Marcus (Project Manager) | **Reviewer:** Elena (Business Analyst)

**Sub-tasks:**
- [ ] **6.2.1** Rate Limiting Implementation
  - [ ] Add Redis-based rate limiting (`backend/guardrails/rate_limiter.py`)
  - [ ] Per-user limits: 100 requests/hour, 10 requests/minute
  - [ ] Per-tenant limits: 1000 requests/hour
  - [ ] Per-session limits: 50 requests/hour
  - [ ] Return 429 with retry-after header

- [ ] **6.2.2** Policy Engine (Open Policy Agent)
  - [ ] Deploy OPA server or use OPA-as-a-Service
  - [ ] Create policy files for tool call restrictions:
    - [ ] `policies/tool_call_policy.rego` - No delete operations
    - [ ] `policies/external_access_policy.rego` - No external emails/APIs
    - [ ] `policies/data_access_policy.rego` - Tenant-scoped data access
  - [ ] Integrate OPA client into `backend/guardrails/policy_engine.py`
  - [ ] Validate tool calls before execution

- [ ] **6.2.3** Cost Limits
  - [ ] Track token usage per session in workflow state
  - [ ] Implement cost calculation (tokens × model cost)
  - [ ] Add session cost limits: $2.00 per session, $10.00 per user/day
  - [ ] Auto-terminate workflow if limit exceeded
  - [ ] Alert on cost threshold (80% of limit)

**Acceptance Criteria:**
- Rate limits enforced at API level
- Tool calls validated against OPA policies
- Cost limits prevent "denial of wallet" scenarios
- All violations logged with user/tenant context

**Files to Create/Modify:**
- `backend/guardrails/rate_limiter.py` (new)
- `backend/guardrails/policy_engine.py` (new)
- `policies/tool_call_policy.rego` (new)
- `policies/external_access_policy.rego` (new)
- `backend/workflows/agent_workflow.py` (modify - add cost tracking)

---

#### Task 6.3: Output Guardrails
**Priority:** High | **Effort:** 1 week | **Dependencies:** 6.1 | **Owner:** Elena (Business Analyst) | **Reviewer:** Marcus (Project Manager) | **Owner:** Elena (Business Analyst) | **Reviewer:** Marcus (Project Manager)

**Sub-tasks:**
- [ ] **6.3.1** Hallucination Detection
  - [ ] Implement LLM-as-Judge pattern (`backend/guardrails/hallucination_detector.py`)
  - [ ] Use GPT-4o-mini or Claude Haiku as judge (cost-effective)
  - [ ] Compare agent output against retrieved context
  - [ ] Score: 0.0 (hallucination) to 1.0 (grounded)
  - [ ] Flag outputs with score < 0.7

- [ ] **6.3.2** Topic/Tone Filtering
  - [ ] Create topic classifier for out-of-scope responses
  - [ ] Filter inappropriate language using content moderation API
  - [ ] Block competitor information if not authorized
  - [ ] Prevent financial/medical advice if not authorized

- [ ] **6.3.3** Output Validation Pipeline
  - [ ] Create `OutputGuardrails` class
  - [ ] Integrate into agent response pipeline
  - [ ] Return sanitized output or request human review
  - [ ] Log all filtered outputs for audit

**Acceptance Criteria:**
- Hallucinations detected with >90% accuracy
- Out-of-scope topics filtered automatically
- All filtered outputs logged and reviewed
- Human escalation for high-risk outputs

**Files to Create/Modify:**
- `backend/guardrails/hallucination_detector.py` (new)
- `backend/guardrails/output_guard.py` (new)
- `backend/agents/base.py` (modify - add output validation)

---

#### Task 6.4: Circuit Breaker Pattern
**Priority:** Medium | **Effort:** 0.5 weeks | **Dependencies:** 6.2, 6.3 | **Owner:** Marcus (Project Manager) | **Reviewer:** Elena (Business Analyst) | **Owner:** Marcus (Project Manager) | **Reviewer:** Elena (Business Analyst)

**Sub-tasks:**
- [ ] **6.4.1** Circuit Breaker Implementation
  - [ ] Create `backend/guardrails/circuit_breaker.py`
  - [ ] Track consecutive failures per session
  - [ ] Trip after 3 consecutive failures
  - [ ] Track low confidence scores (< 0.5)
  - [ ] Trip on cost threshold exceeded

- [ ] **6.4.2** Human Escalation
  - [ ] Create escalation workflow (`backend/workflows/escalation_workflow.py`)
  - [ ] Send notification to human operator
  - [ ] Store session state for review
  - [ ] Allow human to resume or terminate

**Acceptance Criteria:**
- Circuit breaker trips on failure patterns
- Human escalation triggered automatically
- Session state preserved for review
- Metrics tracked for circuit breaker events

**Files to Create/Modify:**
- `backend/guardrails/circuit_breaker.py` (new)
- `backend/workflows/escalation_workflow.py` (new)

---

#### Task 6.5: Compliance Mapping
**Priority:** Medium | **Effort:** 1 week | **Dependencies:** 6.1-6.4 | **Owner:** Elena (Business Analyst) | **Reviewer:** Marcus (Project Manager) | **Owner:** Elena (Business Analyst) | **Reviewer:** Marcus (Project Manager)

**Sub-tasks:**
- [ ] **6.5.1** NIST AI RMF Mapping
  - [ ] Map existing controls to NIST AI RMF categories
  - [ ] Document risk assessment for each agent capability
  - [ ] Create compliance dashboard (`frontend/src/pages/Admin/Compliance.tsx`)
  - [ ] Generate compliance reports

- [ ] **6.5.2** ASL-3 Preparation (if needed)
  - [ ] Assess if ASL-3 is required for use case
  - [ ] Implement real-time classifiers if needed
  - [ ] Add offline monitors for CBRN threats

**Acceptance Criteria:**
- All guardrails mapped to NIST AI RMF
- Compliance dashboard shows current posture
- Risk assessments documented for each layer

**Files to Create/Modify:**
- `docs/compliance/nist-ai-rmf-mapping.md` (new)
- `frontend/src/pages/Admin/Compliance.tsx` (new)

---

## Phase 2: Production Reliability (Weeks 5-8)

### Layer 3: Cognition - LLM Gateway & Reasoning

#### Task 3.1: LLM Gateway Implementation
**Priority:** High | **Effort:** 2 weeks | **Dependencies:** None | **Owner:** Marcus (Project Manager) | **Reviewer:** Elena (Business Analyst)

**Sub-tasks:**
- [ ] **3.1.1** Deploy LiteLLM Gateway
  - [ ] Set up LiteLLM server (`backend/llm/gateway.py`)
  - [ ] Configure provider fallback chains (Azure → Anthropic → Gemini)
  - [ ] Add load balancing across deployments
  - [ ] Implement health checks for each provider

- [ ] **3.1.2** Smart Routing
  - [ ] Create query complexity analyzer (`backend/llm/complexity_analyzer.py`)
  - [ ] Route simple tasks to GPT-4o-mini/Claude Haiku
  - [ ] Route complex reasoning to GPT-4o/Claude Sonnet
  - [ ] Route code generation to specialized models
  - [ ] Add routing rules configuration

- [ ] **3.1.3** Cost Optimization
  - [ ] Track costs per model/provider
  - [ ] Implement cost-based routing (prefer cheaper models when appropriate)
  - [ ] Add cost dashboards (`frontend/src/pages/Admin/CostGovernance.tsx`)

**Acceptance Criteria:**
- All LLM calls go through gateway
- Smart routing reduces costs by 40%+
- Fallback works automatically on provider failures
- Cost tracking accurate to $0.01

**Files to Create/Modify:**
- `backend/llm/gateway.py` (new)
- `backend/llm/complexity_analyzer.py` (new)
- `backend/agents/base.py` (modify - use gateway)
- `frontend/src/pages/Admin/CostGovernance.tsx` (new)

---

#### Task 3.2: Structured Output Enforcement
**Priority:** High | **Effort:** 1 week | **Dependencies:** 3.1 | **Owner:** Elena (Business Analyst) | **Reviewer:** Marcus (Project Manager)

**Sub-tasks:**
- [ ] **3.2.1** PydanticAI Integration
  - [ ] Install and configure PydanticAI
  - [ ] Define output schemas for all agent responses
  - [ ] Create `backend/agents/schemas.py` with response types
  - [ ] Integrate into agent base class

- [ ] **3.2.2** Self-Correction on Validation Failure
  - [ ] Catch validation errors
  - [ ] Feed errors back to model with correction prompt
  - [ ] Retry up to 3 times
  - [ ] Log validation failures for analysis

**Acceptance Criteria:**
- All agent outputs validated against schemas
- Validation failures trigger self-correction
- <5% of responses require manual correction
- Type-safe responses throughout system

**Files to Create/Modify:**
- `backend/agents/schemas.py` (new)
- `backend/agents/base.py` (modify - add PydanticAI)

---

#### Task 3.3: Advanced Reasoning Patterns
**Priority:** Medium | **Effort:** 1 week | **Dependencies:** 3.2 | **Owner:** Elena (Business Analyst) | **Reviewer:** Marcus (Project Manager)

**Sub-tasks:**
- [ ] **3.3.1** ReAct Loop Implementation
  - [ ] Add explicit ReAct pattern to agent reasoning
  - [ ] Capture thought/action/observation steps
  - [ ] Store reasoning trace for debugging
  - [ ] Add ReAct visualization in UI

- [ ] **3.3.2** Chain-of-Thought Enforcement
  - [ ] Add CoT prompting for complex tasks
  - [ ] Capture reasoning steps in response
  - [ ] Display reasoning in UI (collapsible)

**Acceptance Criteria:**
- ReAct loop visible in agent traces
- Reasoning steps captured and displayable
- Improved accuracy on multi-step tasks

**Files to Create/Modify:**
- `backend/agents/reasoning.py` (new)
- `frontend/src/components/Agent/ReasoningTrace.tsx` (new)

---

### Layer 7: Observability - Evaluation & LLMOps

#### Task 7.1: LLMOps Platform Integration
**Priority:** High | **Effort:** 1.5 weeks | **Dependencies:** None | **Owner:** Marcus (Project Manager) | **Reviewer:** Elena (Business Analyst)

**Sub-tasks:**
- [ ] **7.1.1** Arize Phoenix Deployment
  - [ ] Deploy Phoenix server or use cloud service
  - [ ] Integrate Phoenix SDK into agent workflows
  - [ ] Send execution traces to Phoenix
  - [ ] Configure trace visualization

- [ ] **7.1.2** LangSmith Integration (optional)
  - [ ] Add LangSmith for debugging agent paths
  - [ ] Enable trace replay for failure analysis
  - [ ] Add LangSmith UI to admin panel

**Acceptance Criteria:**
- All agent executions traced in Phoenix
- Trace visualization shows full execution path
- Can replay traces for debugging
- Performance metrics visible in dashboard

**Files to Create/Modify:**
- `backend/observability/phoenix.py` (new)
- `backend/workflows/agent_workflow.py` (modify - add Phoenix tracing)

---

#### Task 7.2: Evaluation Framework
**Priority:** High | **Effort:** 1.5 weeks | **Dependencies:** 7.1 | **Owner:** Elena (Business Analyst) | **Reviewer:** Marcus (Project Manager)

**Sub-tasks:**
- [ ] **7.2.1** DeepEval Integration
  - [ ] Install DeepEval framework
  - [ ] Create golden datasets (`tests/evals/golden_datasets/`)
  - [ ] Define evaluation metrics:
    - [ ] Faithfulness (hallucination detection)
    - [ ] Answer Relevance
    - [ ] Context Precision
    - [ ] Response Completeness
  - [ ] Create eval test suite (`tests/evals/test_agent_quality.py`)

- [ ] **7.2.2** Continuous Evaluation in CI/CD
  - [ ] Add eval step to GitHub Actions
  - [ ] Run evals on every PR
  - [ ] Block merge if evals fail
  - [ ] Track eval scores over time

- [ ] **7.2.3** Online Evaluation (LLM-as-Judge)
  - [ ] Sample 10% of production interactions
  - [ ] Use GPT-4o as judge for quality scoring
  - [ ] Track quality drift over time
  - [ ] Alert on quality degradation

**Acceptance Criteria:**
- Golden dataset with 50+ test cases
- Eval pipeline runs in CI/CD
- Quality metrics tracked in dashboard
- Alerts on quality degradation

**Files to Create/Modify:**
- `tests/evals/golden_datasets/` (new directory)
- `tests/evals/test_agent_quality.py` (new)
- `.github/workflows/evals.yml` (new)
- `backend/observability/quality_monitor.py` (new)

---

#### Task 7.3: Cost Governance
**Priority:** Medium | **Effort:** 1 week | **Dependencies:** 3.1 | **Owner:** Marcus (Project Manager) | **Reviewer:** Elena (Business Analyst)

**Sub-tasks:**
- [ ] **7.3.1** Per-Session Cost Tracking
  - [ ] Track costs in workflow state
  - [ ] Store costs in database
  - [ ] Create cost aggregation queries

- [ ] **7.3.2** Cost Dashboards
  - [ ] Create cost dashboard (`frontend/src/pages/Admin/CostGovernance.tsx`)
  - [ ] Show costs per user/tenant/session
  - [ ] Add cost trends over time
  - [ ] Implement cost alerts

- [ ] **7.3.3** Hard Budget Caps
  - [ ] Implement session cost limits (from Layer 6)
  - [ ] Add user/tenant daily limits
  - [ ] Auto-terminate on limit exceeded

**Acceptance Criteria:**
- Cost tracking accurate to $0.01
- Dashboards show real-time costs
- Budget caps enforced automatically
- Alerts sent on threshold breaches

**Files to Create/Modify:**
- `backend/guardrails/cost_tracker.py` (new)
- `frontend/src/pages/Admin/CostGovernance.tsx` (modify - enhance)

---

## Phase 3: Advanced Capabilities (Weeks 9-12)

### Layer 1: Interaction - Generative UI & HITL

#### Task 1.1: Generative UI Component System
**Priority:** High | **Effort:** 2 weeks | **Dependencies:** None | **Owner:** Elena (Business Analyst) | **Reviewer:** Marcus (Project Manager)

**Sub-tasks:**
- [ ] **1.1.1** Component Schema System
  - [ ] Define Zod schemas for UI components
  - [ ] Create component registry (`frontend/src/components/GenUI/registry.ts`)
  - [ ] Implement typed components:
    - [ ] `<DataTable />` - For tabular data
    - [ ] `<Chart />` - For visualizations
    - [ ] `<ApprovalCard />` - For HITL approvals
    - [ ] `<Timeline />` - For workflow visualization
    - [ ] `<Form />` - For structured inputs

- [ ] **1.1.2** Agent Output Parser
  - [ ] Create parser for structured JSON payloads
  - [ ] Validate against Zod schemas
  - [ ] Render components dynamically
  - [ ] Handle fallback to markdown for unstructured output

- [ ] **1.1.3** Component Library
  - [ ] Build reusable GenUI components
  - [ ] Add styling and animations
  - [ ] Test component rendering
  - [ ] Document component usage

**Acceptance Criteria:**
- Agents can output structured UI payloads
- Components render correctly from JSON
- Fallback to markdown works seamlessly
- Component library documented

**Files to Create/Modify:**
- `frontend/src/components/GenUI/registry.ts` (new)
- `frontend/src/components/GenUI/DataTable.tsx` (new)
- `frontend/src/components/GenUI/Chart.tsx` (new)
- `frontend/src/components/Chat/ChatMessage.tsx` (modify - add GenUI support)

---

#### Task 1.2: Advanced Streaming
**Priority:** Medium | **Effort:** 1 week | **Dependencies:** 1.1 | **Owner:** Marcus (Project Manager) | **Reviewer:** Elena (Business Analyst)

**Sub-tasks:**
- [ ] **1.2.1** Separate Streams for Text vs Structure
  - [ ] Create separate WebSocket channels for text and UI updates
  - [ ] Stream text tokens for conversational elements
  - [ ] Stream structural updates for UI components
  - [ ] Sync streams on frontend

- [ ] **1.2.2** Progressive Rendering
  - [ ] Render charts/tables incrementally as data arrives
  - [ ] Show loading states for incomplete components
  - [ ] Add smooth transitions

- [ ] **1.2.3** Optimistic UI Updates
  - [ ] Implement optimistic updates for form submissions
  - [ ] Rollback on error
  - [ ] Show pending states

**Acceptance Criteria:**
- Text and UI streams work independently
- Components render progressively
- Optimistic updates improve perceived latency
- Error handling graceful

**Files to Create/Modify:**
- `backend/api/routers/chat.py` (modify - add separate streams)
- `frontend/src/hooks/useChatStream.ts` (modify - handle dual streams)

---

#### Task 1.3: Complete HITL UI
**Priority:** High | **Effort:** 1 week | **Dependencies:** 1.1 | **Owner:** Elena (Business Analyst) | **Reviewer:** Marcus (Project Manager)

**Sub-tasks:**
- [ ] **1.3.1** Pending Approvals Component
  - [ ] Create `frontend/src/pages/Workflows/PendingApprovals.tsx`
  - [ ] List all workflows waiting for approval
  - [ ] Show approval context and proposed actions
  - [ ] Implement approve/reject/edit actions

- [ ] **1.3.2** Parameter Editing UI
  - [ ] Create parameter editor component
  - [ ] Allow editing tool call parameters before execution
  - [ ] Validate edited parameters
  - [ ] Submit edited parameters to workflow

- [ ] **1.3.3** Real-Time Workflow Status
  - [ ] Add WebSocket connection for workflow updates
  - [ ] Show live status in UI
  - [ ] Display current step and progress

**Acceptance Criteria:**
- Users can see and approve pending workflows
- Tool parameters editable before execution
- Real-time workflow status visible
- HITL flows complete end-to-end

**Files to Create/Modify:**
- `frontend/src/pages/Workflows/PendingApprovals.tsx` (new)
- `frontend/src/components/Workflows/ParameterEditor.tsx` (new)
- `frontend/src/pages/Workflows/ActiveWorkflows.tsx` (modify - add real-time updates)

---

### Layer 4: Memory - GraphRAG & Context Optimization

#### Task 4.1: GraphRAG Implementation
**Priority:** High | **Effort:** 2 weeks | **Dependencies:** None | **Owner:** Elena (Business Analyst) | **Reviewer:** Marcus (Project Manager)

**Sub-tasks:**
- [ ] **4.1.1** Knowledge Graph Setup
  - [ ] Deploy Graphiti (Zep's knowledge graph) or KuzuDB
  - [ ] Create entity extraction pipeline
  - [ ] Extract entities during document ingestion
  - [ ] Store relationships in graph

- [ ] **4.1.2** Multi-Hop Traversal
  - [ ] Implement graph traversal queries
  - [ ] Support multi-hop relationship queries
  - [ ] Add graph query API endpoint
  - [ ] Integrate into memory search

- [ ] **4.1.3** Hybrid Search
  - [ ] Add BM25 keyword search
  - [ ] Combine vector + keyword + graph search
  - [ ] Implement result fusion algorithm
  - [ ] Tune retrieval based on query type

**Acceptance Criteria:**
- Knowledge graph stores entities and relationships
- Multi-hop queries work correctly
- Hybrid search improves retrieval accuracy
- Graph queries integrated into agent memory

**Files to Create/Modify:**
- `backend/memory/graph.py` (new)
- `backend/memory/client.py` (modify - add graph search)
- `backend/api/routers/memory.py` (modify - add graph endpoints)

---

#### Task 4.2: Context Optimization
**Priority:** Medium | **Effort:** 1 week | **Dependencies:** 4.1 | **Owner:** Elena (Business Analyst) | **Reviewer:** Marcus (Project Manager)

**Sub-tasks:**
- [ ] **4.2.1** Automatic Summarization
  - [ ] Implement summarization after N turns (e.g., 20)
  - [ ] Preserve key decisions and state changes
  - [ ] Store summaries in session metadata
  - [ ] Use summaries for context injection

- [ ] **4.2.2** Rolling Window Pattern
  - [ ] Keep last N messages verbatim (e.g., 10)
  - [ ] Summarize older messages
  - [ ] Inject summary + recent messages into context
  - [ ] Implement anchor summarization for long conversations

- [ ] **4.2.3** Context Trimming
  - [ ] Detect task boundaries
  - [ ] Remove completed task details from context
  - [ ] Keep only relevant context for current task
  - [ ] Monitor context window usage

**Acceptance Criteria:**
- Summarization reduces context size by 60%+
- Rolling window maintains recent context verbatim
- Context trimming improves relevance
- Context window usage optimized

**Files to Create/Modify:**
- `backend/memory/context_optimizer.py` (new)
- `backend/agents/base.py` (modify - use optimized context)

---

## Phase 4: Enterprise Polish (Weeks 13-16)

### Layer 2: Orchestration - Advanced Patterns

#### Task 2.1: Enhanced Self-Correction
**Priority:** Medium | **Effort:** 1 week | **Dependencies:** 3.3 | **Owner:** Marcus (Project Manager) | **Reviewer:** Elena (Business Analyst)

**Sub-tasks:**
- [ ] **2.1.1** Explicit ReAct Loop
  - [ ] Implement ReAct pattern in agent reasoning (from Layer 3)
  - [ ] Add tool output parsing with error detection
  - [ ] Enable retry with alternative strategy on failures
  - [ ] Log self-correction attempts

- [ ] **2.1.2** Error Recovery
  - [ ] Detect tool execution failures
  - [ ] Analyze error messages
  - [ ] Generate alternative strategies
  - [ ] Retry with new approach

**Acceptance Criteria:**
- ReAct loop visible in agent execution
- Self-correction works on tool failures
- Alternative strategies attempted automatically
- Success rate improves by 10%+

**Files to Create/Modify:**
- `backend/agents/base.py` (modify - enhance ReAct loop)

---

#### Task 2.2: Hierarchical Agent Planning
**Priority:** Medium | **Effort:** 1.5 weeks | **Dependencies:** 2.1 | **Owner:** Marcus (Project Manager) | **Reviewer:** Elena (Business Analyst)

**Sub-tasks:**
- [ ] **2.2.1** Planner Agent
  - [ ] Create `PlannerAgent` class
  - [ ] Decompose complex goals into milestones
  - [ ] Generate execution plan
  - [ ] Track milestone completion

- [ ] **2.2.2** Milestone Tracking
  - [ ] Store milestones in workflow state
  - [ ] Update milestones as tasks complete
  - [ ] Display milestones in UI
  - [ ] Alert on milestone delays

**Acceptance Criteria:**
- Planner agent creates execution plans
- Milestones tracked and visible
- Complex goals broken down correctly
- Plan execution monitored

**Files to Create/Modify:**
- `backend/agents/planner.py` (new)
- `frontend/src/components/Workflows/Milestones.tsx` (new)

---

#### Task 2.3: State Persistence & Branching
**Priority:** High | **Effort:** 1.5 weeks | **Dependencies:** None | **Owner:** Marcus (Project Manager) | **Reviewer:** Elena (Business Analyst)

**Sub-tasks:**
- [ ] **2.3.1** State Persistence
  - [ ] Migrate from in-memory dict to Redis/PostgreSQL
  - [ ] Store session state in database
  - [ ] Implement state serialization/deserialization
  - [ ] Add state versioning

- [ ] **2.3.2** State Branching
  - [ ] Implement state forking for "what-if" scenarios
  - [ ] Create branch from current state
  - [ ] Execute alternative paths
  - [ ] Compare branch outcomes
  - [ ] Merge or discard branches

- [ ] **2.3.3** Time Travel Debugging
  - [ ] Use Temporal history for state replay
  - [ ] Create UI for state inspection
  - [ ] Allow rewinding to previous states
  - [ ] Replay from any point

**Acceptance Criteria:**
- State persists across restarts
- State branching works for what-if scenarios
- Time travel debugging functional
- State versioning prevents data loss

**Files to Create/Modify:**
- `backend/orchestration/state_store.py` (new)
- `backend/orchestration/state_branching.py` (new)
- `frontend/src/pages/Workflows/StateInspector.tsx` (new)

---

### Layer 5: Tools - Sandboxing & Validation

#### Task 5.1: Sandboxed Code Execution
**Priority:** Medium | **Effort:** 2 weeks | **Dependencies:** 6.2 (policy engine) | **Owner:** Marcus (Project Manager) | **Reviewer:** Elena (Business Analyst)

**Sub-tasks:**
- [ ] **5.1.1** E2B Integration
  - [ ] Set up E2B account and API keys
  - [ ] Create `backend/tools/code_executor.py`
  - [ ] Implement sandbox creation and destruction
  - [ ] Add code execution with timeouts

- [ ] **5.1.2** Code Execution Tool
  - [ ] Create `execute_code` tool for agents
  - [ ] Support Python, JavaScript, SQL
  - [ ] Return execution results or errors
  - [ ] Add data analysis capabilities (CSV processing, calculations)

- [ ] **5.1.3** Security & Isolation
  - [ ] Implement network isolation
  - [ ] Add execution timeouts (30s default)
  - [ ] Restrict file system access
  - [ ] Log all code executions

**Acceptance Criteria:**
- Agents can execute code safely
- Sandboxes isolated from host
- Timeouts prevent infinite loops
- All executions logged and auditable

**Files to Create/Modify:**
- `backend/tools/code_executor.py` (new)
- `backend/agents/tools.py` (modify - add execute_code)

---

#### Task 5.2: Tool Validation Middleware
**Priority:** High | **Effort:** 1 week | **Dependencies:** 5.1 | **Owner:** Marcus (Project Manager) | **Reviewer:** Elena (Business Analyst)

**Sub-tasks:**
- [ ] **5.2.1** Pre-Execution Validation
  - [ ] Create validation middleware layer
  - [ ] Validate tool parameters against schemas
  - [ ] Check parameter types and ranges
  - [ ] Generate structured errors on failure

- [ ] **5.2.2** Agent Self-Healing
  - [ ] Feed validation errors back to agent
  - [ ] Allow agent to correct parameters
  - [ ] Retry with corrected parameters
  - [ ] Log self-healing attempts

- [ ] **5.2.3** Parameter Sanitization
  - [ ] Sanitize all tool parameters
  - [ ] Prevent injection attacks
  - [ ] Validate file paths
  - [ ] Check resource limits

**Acceptance Criteria:**
- All tool calls validated before execution
- Validation errors trigger self-healing
- Parameter sanitization prevents attacks
- Self-healing success rate >80%

**Files to Create/Modify:**
- `backend/tools/validation.py` (new)
- `backend/agents/base.py` (modify - add validation middleware)

---

## Implementation Timeline

```
Week 1-4:   Phase 1 - Critical Security (Layer 6)
Week 5-8:   Phase 2 - Production Reliability (Layers 3, 7)
Week 9-12:  Phase 3 - Advanced Capabilities (Layers 1, 4)
Week 13-16: Phase 4 - Enterprise Polish (Layers 2, 5)
```

## Dependencies Map

```
Layer 6 (Guardrails) → All other layers (must be first)
Layer 3 (Cognition) → Layer 7 (Observability) - cost tracking
Layer 1 (Interaction) → Layer 2 (Orchestration) - HITL workflows
Layer 4 (Memory) → Layer 3 (Cognition) - context injection
Layer 5 (Tools) → Layer 6 (Guardrails) - policy enforcement
```

## Success Metrics

### Layer 6: Guardrails
- ✅ 100% of inputs pass through guardrails
- ✅ 0 prompt injection successes
- ✅ 100% PII redaction rate
- ✅ <1% false positive rate

### Layer 3: Cognition
- ✅ 40%+ cost reduction via smart routing
- ✅ 99.9%+ uptime via fallback chains
- ✅ <5% validation failure rate

### Layer 7: Observability
- ✅ 100% of executions traced
- ✅ Golden dataset with 50+ test cases
- ✅ Quality metrics tracked daily

### Layer 1: Interaction
- ✅ GenUI components render correctly
- ✅ HITL approval time <5 minutes
- ✅ Streaming latency <300ms

### Layer 4: Memory
- ✅ 60%+ context size reduction
- ✅ Multi-hop queries work correctly
- ✅ Hybrid search improves accuracy

### Layer 2: Orchestration
- ✅ State persists across restarts
- ✅ Self-correction success rate >80%
- ✅ Time travel debugging functional

### Layer 5: Tools
- ✅ Code execution isolated
- ✅ Validation prevents 95%+ errors
- ✅ Self-healing success rate >80%

---

## Risk Mitigation

### High-Risk Areas
1. **Layer 6 Implementation** - Critical for security, must be done first
2. **State Migration** - Risk of data loss during migration
3. **Cost Tracking** - Must be accurate to prevent budget overruns

### Mitigation Strategies
- Implement Layer 6 in stages with testing at each stage
- Use feature flags for gradual rollout
- Backup state before migration
- Monitor costs closely during implementation
- Set up alerts for anomalies

---

## Next Steps

1. **Review this plan** with team
2. **Prioritize tasks** based on business needs
3. **Assign owners** for each task
4. **Set up project tracking** (GitHub Projects, Jira, etc.)
5. **Begin Phase 1** - Critical Security (Layer 6)

---

*Last Updated: December 20, 2024*  
*Document Version: 1.0*

