#!/usr/bin/env python3
"""
Ingest Agentic Framework to Azure Production

Directly ingests the 7-Layer Production-Grade Agentic System framework and
maturity assessment into the Azure Zep instance at zep.engram.work.

Usage:
    python -m backend.scripts.ingest_agentic_framework_azure
"""

import httpx
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ZEP_URL = 'https://zep.engram.work'

# Agentic Framework Knowledge Sessions
AGENTIC_FRAMEWORK_SESSIONS = [
    {
        "session_id": "sess-agentic-framework-001",
        "user_id": "user-derek",
        "metadata": {
            "summary": "FOUNDATIONAL: Production-Grade Agentic System Layers framework - 7-layer architecture for enterprise AI systems. Defines Interaction, Orchestration, Cognition, Memory, Tools, Guardrails, and Observability layers.",
            "agent_id": "elena",
            "topics": ["Architecture", "Agentic AI", "Framework", "Production-Grade", "7-Layers"],
            "priority": "critical",
        },
        "messages": [
            {"role_type": "user", "content": "Elena, we need to understand the Production-Grade Agentic System Layers framework. This is the gold standard for building enterprise AI agents."},
            {"role_type": "assistant", "content": "I've analyzed the 7-Layer framework. It represents the most significant advancement in agentic AI architecture since cloud computing. Each layer addresses a critical capability gap between demos and production systems."},
            {"role_type": "user", "content": "What are the 7 layers?"},
            {"role_type": "assistant", "content": """The 7 layers are:

**Layer 1 - Interaction**: Generative UI (GenUI), streaming, Human-in-the-Loop patterns
**Layer 2 - Orchestration**: Cyclic graphs, durable execution (Temporal/LangGraph), multi-agent coordination
**Layer 3 - Cognition**: LLM Gateway routing, advanced reasoning (ReAct, CoT), structured outputs
**Layer 4 - Memory**: GraphRAG, context engineering, episodic vs semantic memory, data isolation
**Layer 5 - Tools**: MCP protocol, sandboxed execution (E2B), schema validation
**Layer 6 - Guardrails**: Input/output guardrails, policy enforcement (OPA), circuit breakers
**Layer 7 - Observability**: Distributed tracing (OpenTelemetry), evals (DeepEval), cost governance

The key insight is wrapping the nondeterministic LLM core in deterministic control structures."""},
            {"role_type": "user", "content": "Marcus, what's the implementation priority?"},
            {"role_type": "assistant", "content": "From a project management perspective, Layer 6 (Guardrails) is the most critical gap for production readiness. Without prompt injection detection, PII redaction, and circuit breakers, enterprise deployment is risky. I recommend the phased approach: 1) Security first (weeks 1-4), 2) Reliability (weeks 5-8), 3) Advanced features (weeks 9-12), 4) Polish (weeks 13-16)."},
            {"role_type": "user", "content": "What about the Orchestration layer?"},
            {"role_type": "assistant", "content": "The framework emphasizes that production agents require cyclic graph architectures, not linear chains. The pattern is: Reason → Act → Observe → Decide (loop or exit). Critically, durable execution via Temporal or LangGraph checkpointing ensures workflows survive crashes and can 'time travel' for debugging."},
            {"role_type": "assistant", "content": "We already have strong implementation here with Temporal integration. Our AgentWorkflow class uses event sourcing with automatic replay. The gaps are explicit ReAct implementation and state branching for 'what-if' scenarios."},
            {"role_type": "user", "content": "What about the Memory layer and GraphRAG?"},
            {"role_type": "assistant", "content": "Standard RAG fails on complex queries requiring multi-hop reasoning. GraphRAG stores entities and relationships in a knowledge graph, enabling traversal queries. The framework recommends hybrid search: BM25 (keyword) + Vector (semantic) + Graph (structural). Zep's Graphiti is the recommended solution for this."},
            {"role_type": "user", "content": "Key takeaway for our team?"},
            {"role_type": "assistant", "content": "The framework's core message is 'Stop Vibe Coding'. Production systems require rigorous engineering: strict tool schemas, deterministic orchestration wrapping probabilistic LLMs, comprehensive guardrails, and observable traces. We must evolve from 'LLM wrappers' to 'cognitive architectures'."},
            {"role_type": "assistant", "content": "For timelines: a well-architected system following this framework takes 16 weeks to reach full maturity. We're ahead on Orchestration (Layer 2) and Tools (Layer 5), but behind on Guardrails (Layer 6). I'll track the detailed implementation plan as a project milestone."},
        ]
    },
    {
        "session_id": "sess-maturity-assessment-001",
        "user_id": "user-derek",
        "metadata": {
            "summary": "CRITICAL: Engram System Maturity Assessment - Current score 2.71/5.0. Layer 6 (Guardrails) at 0.8/5.0 is the critical gap. 16-week roadmap to full production maturity defined.",
            "agent_id": "elena",
            "topics": ["Assessment", "Maturity", "Gaps", "Roadmap", "Production-Readiness"],
            "priority": "critical",
        },
        "messages": [
            {"role_type": "user", "content": "We've completed a maturity assessment against the 7-layer framework. What are the results?"},
            {"role_type": "assistant", "content": """The overall system maturity is **2.71/5.0** (⭐⭐⭐☆☆).

**Layer Scores:**
- Layer 1 (Interaction): 3.0/5.0
- Layer 2 (Orchestration): 3.75/5.0 ← Strongest
- Layer 3 (Cognition): 2.67/5.0
- Layer 4 (Memory): 3.33/5.0
- Layer 5 (Tools): 3.0/5.0
- Layer 6 (Guardrails): 0.8/5.0 ⚠️ CRITICAL GAP
- Layer 7 (Observability): 3.0/5.0

The Guardrails layer is our most urgent priority."""},
            {"role_type": "user", "content": "What are our strengths?"},
            {"role_type": "assistant", "content": """Our key strengths are:

1. **Durable Execution (5/5)**: Full Temporal integration with AgentWorkflow, ConversationWorkflow, retry policies, and signals for HITL.

2. **MCP Protocol (5/5)**: Complete FastMCP implementation with chat, memory, ingestion, and workflow tools exposed via SSE.

3. **State Management (4/5)**: 4-layer EnterpriseContext schema with Security, Episodic, Semantic, and Operational layers.

4. **OpenTelemetry (4/5)**: Azure Monitor integration with trace_function decorators and TelemetryMiddleware."""},
            {"role_type": "user", "content": "Marcus, what are the critical gaps and timeline?"},
            {"role_type": "assistant", "content": """Critical gaps requiring immediate attention:

**Layer 6 Guardrails (0.8/5.0)** - PRODUCTION BLOCKER:
- No prompt injection detection
- No PII redaction
- No circuit breaker pattern
- No output hallucination detection
- No rate limiting per tenant

**Recommended Tools:**
- Rebuff or Presidio for PII
- Open Policy Agent (OPA) for policies
- LLM-as-Judge pattern for output validation

Timeline: 4 weeks to address critical security gaps."""},
            {"role_type": "user", "content": "What about cognitive capabilities?"},
            {"role_type": "assistant", "content": """Layer 3 (Cognition) scored 2.67/5.0 with these gaps:

1. **No LLM Gateway**: We have individual clients (Azure, Gemini, Claude) but no centralized gateway for smart routing and fallbacks. Recommend LiteLLM.

2. **No Structured Output Enforcement**: Agents return plain text. We need PydanticAI-style type-safe outputs with auto-retry on validation failure.

3. **No ReAct Pattern**: Missing explicit Thought→Action→Observation loops for complex reasoning.

Timeline: Weeks 5-8 for LLM Gateway and structured outputs."""},
            {"role_type": "user", "content": "What about the Memory layer?"},
            {"role_type": "assistant", "content": """Layer 4 (Memory) scored 3.33/5.0:

**Current State:**
- Zep integration with semantic search ✅
- Episodic + Semantic memory enrichment ✅
- Session isolation via SecurityContext ✅

**Gaps:**
- No GraphRAG/multi-hop traversal
- No automatic context summarization
- No hybrid BM25+vector search

**Recommendation:** Deploy Graphiti for knowledge graphs, implement rolling window compression."""},
            {"role_type": "user", "content": "Give me the 16-week roadmap."},
            {"role_type": "assistant", "content": """**Phase 1: Critical Security (Weeks 1-4)** - Focus: Layer 6
- [ ] Prompt injection detection
- [ ] PII redaction middleware
- [ ] Rate limiting per tenant
- [ ] Circuit breaker pattern
- [ ] Session cost limits

**Phase 2: Production Reliability (Weeks 5-8)** - Focus: Layers 3+7
- [ ] Deploy LiteLLM Gateway
- [ ] Integrate DeepEval framework
- [ ] Add PydanticAI structured outputs
- [ ] Cost governance dashboards

**Phase 3: Advanced Capabilities (Weeks 9-12)** - Focus: Layers 1+4
- [ ] Generative UI component system
- [ ] Deploy GraphRAG (Graphiti)
- [ ] Context compression
- [ ] HITL approval UI

**Phase 4: Enterprise Polish (Weeks 13-16)** - Focus: Layers 2+5
- [ ] Hierarchical agent planning
- [ ] State branching (what-if)
- [ ] E2B sandboxed execution
- [ ] NIST AI RMF compliance"""},
            {"role_type": "user", "content": "How should we track progress?"},
            {"role_type": "assistant", "content": "I recommend using this session (sess-maturity-assessment-001) as the baseline. After each phase, we create a follow-up session documenting what was implemented and the updated maturity scores. The goal is to reach 4.5/5.0 overall within 16 weeks."},
            {"role_type": "assistant", "content": "I'll reference this assessment when discussing any layer improvements. When asked about architecture decisions, I can now ground my recommendations in our specific gaps and the framework's best practices. This is recursive self-awareness in action - the system knows its own weaknesses and can work to address them."},
            {"role_type": "user", "content": "Store this knowledge permanently. It guides all future development."},
            {"role_type": "assistant", "content": "Understood. This episodic memory is now part of our foundational knowledge. Every conversation about improvements, architecture, or production readiness will draw from this assessment. The 7-layer framework and our maturity scores are embedded in the context engine."},
        ]
    },
    {
        "session_id": "sess-layer6-guardrails-001",
        "user_id": "user-derek",
        "metadata": {
            "summary": "Deep dive on Layer 6 Guardrails implementation. Defines input, execution, and output guardrails with circuit breaker patterns. Critical for production deployment.",
            "agent_id": "elena",
            "topics": ["Guardrails", "Security", "Safety", "Compliance", "Circuit Breaker"],
            "priority": "critical",
        },
        "messages": [
            {"role_type": "user", "content": "Elena, let's deep dive on Layer 6 - Guardrails. This is our biggest gap."},
            {"role_type": "assistant", "content": """Layer 6 operates at three stages of the agentic lifecycle:

**1. Input Guardrails (Pre-Processing)**
- Prompt injection detection: Patterns like 'ignore previous instructions', 'DAN mode'
- PII redaction: Credit cards, SSNs, internal IPs masked before LLM calls
- Implements: Rebuff, Microsoft Presidio, custom regex

**2. Execution Guardrails (Runtime)**
- Rate limiting per user/tenant
- Policy enforcement via Open Policy Agent (OPA)
- Tool call policies: 'agents cannot delete tables', 'no external emails'

**3. Output Guardrails (Post-Processing)**
- Hallucination detection via 'Judge' model
- Topic/tone filtering
- Competitor mention blocking"""},
            {"role_type": "user", "content": "What is the circuit breaker pattern?"},
            {"role_type": "assistant", "content": """The Circuit Breaker is a meta-monitor that tracks agent health:

```python
class CircuitBreaker:
    max_consecutive_failures: int = 3
    cost_limit: float = 5.00  # per session
    confidence_threshold: float = 0.7
    
    def check(session_state) -> bool:
        # Trip conditions:
        # 1. Failed 3+ tasks in a row
        # 2. Session cost exceeded $5
        # 3. Repeated low-confidence outputs
        # Returns: should_halt
```

When tripped, it immediately halts execution and escalates to a human operator. This prevents runaway failures and 'denial of wallet' scenarios."""},
            {"role_type": "user", "content": "Marcus, what's the implementation plan?"},
            {"role_type": "assistant", "content": """Implementation plan for Guardrails layer:

**Week 1: Input Guardrails**
1. Create `backend/guardrails/` directory
2. Implement InputGuard class with:
   - `detect_prompt_injection(text)` 
   - `redact_pii(text)`
   - `validate_input(text) -> GuardResult`
3. Integrate as middleware in FastAPI

**Week 2: Execution Guardrails**
1. Add rate limiter middleware (Redis-backed)
2. Define OPA policies for tool calls
3. Implement per-session cost tracking

**Week 3: Output Guardrails**
1. Create OutputGuard class
2. Implement LLM-as-Judge pattern
3. Add hallucination scoring vs. retrieved context

**Week 4: Circuit Breaker**
1. Implement CircuitBreaker class
2. Add failure tracking per session
3. Create escalation webhook to human operators"""},
            {"role_type": "user", "content": "What tools and libraries should we use?"},
            {"role_type": "assistant", "content": """Recommended tools for guardrails implementation:

**Input Guardrails:**
- [Rebuff](https://github.com/protectai/rebuff) - Prompt injection detection
- [Microsoft Presidio](https://github.com/microsoft/presidio) - PII detection/anonymization

**Execution Guardrails:**
- [Open Policy Agent](https://www.openpolicyagent.org/) - Policy-as-code engine
- Redis for distributed rate limiting

**Output Guardrails:**
- [Galileo](https://galileo.ai) - Hallucination detection
- DeepEval for output quality scoring

**Monitoring:**
- OpenTelemetry for guardrail trace events
- Azure Monitor alerts on circuit breaker trips"""},
            {"role_type": "user", "content": "Why is NIST AI RMF mentioned?"},
            {"role_type": "assistant", "content": """The NIST AI Risk Management Framework (AI RMF) is the emerging gold standard for enterprise AI governance. It defines four core functions:

1. **GOVERN**: Establish policies and accountability
2. **MAP**: Identify and document AI systems and their context
3. **MEASURE**: Assess and track risks
4. **MANAGE**: Prioritize and act on risks

For Engram, we should map our guardrails to NIST categories and document our risk posture. This is critical for enterprise customers in regulated industries (healthcare, finance, government)."""},
        ]
    },
    {
        "session_id": "sess-layer-details-001",
        "user_id": "user-derek",
        "metadata": {
            "summary": "Detailed breakdown of all 7 agentic system layers with specific implementation patterns, tools, and best practices for each layer.",
            "agent_id": "elena",
            "topics": ["Architecture", "Implementation", "Patterns", "Tools", "Best Practices"],
            "priority": "high",
        },
        "messages": [
            {"role_type": "user", "content": "Give me the detailed implementation patterns for each layer."},
            {"role_type": "assistant", "content": """**Layer 1 - Interaction Layer:**

GenUI Patterns:
- **Static GenUI**: Agent selects from predefined components (<StockChart />, <ApprovalCard />)
- **Declarative GenUI**: Agent emits JSON schema, frontend renders dynamically
- **Open-Ended GenUI**: Agent generates raw HTML (security risk - avoid in production)

Streaming: Use SSE or WebSocket for token streaming and structural updates.
HITL: Implement 'pending decision' state with Approve/Reject/Edit options."""},
            {"role_type": "assistant", "content": """**Layer 2 - Orchestration Layer:**

Cyclic Graph Pattern (ReAct):
1. Reasoning Node: LLM analyzes state, decides action
2. Tool Node: Execute selected tool
3. Observation: Feed output back to state
4. Router: Check if complete, or loop back

Durable Execution:
- LangGraph: Checkpointing to Postgres after each node
- Temporal: Event sourcing with history replay

Multi-Agent Patterns:
- Supervisor/Router: Central coordinator delegates to specialists
- Hierarchical: Planning agent breaks goals into milestones
- Network: Direct peer-to-peer (discouraged - hard to debug)"""},
            {"role_type": "assistant", "content": """**Layer 3 - Cognition Layer:**

LLM Gateway:
- Smart routing: Simple tasks → cheap models (GPT-4o-mini)
- Complex tasks → frontier models (GPT-4o, Claude 3.5)
- Fallback chains: Azure → Anthropic → Gemini
- Load balancing across regions

Advanced Reasoning:
- Chain-of-Thought: Explicit reasoning steps before answer
- ReAct: Thought → Action → Observation loop
- Structured Output: PydanticAI with Zod schemas, auto-retry on validation fail"""},
            {"role_type": "assistant", "content": """**Layer 4 - Memory Layer:**

Context Engineering:
- Summarization: Rolling window with compressed old turns
- Anchor Summaries: High-level goal persisted throughout
- Context Trimming: Remove completed task details

GraphRAG:
- Extract entities and relationships during ingestion
- Store in graph DB (Neo4j, KuzuDB, Graphiti)
- Multi-hop queries for complex reasoning

Hybrid Search:
- BM25 for keyword matches
- Vector for semantic similarity
- Graph traversal for relationships"""},
            {"role_type": "assistant", "content": """**Layer 5 - Tools Layer:**

MCP Architecture:
- MCP Host: Application where agent lives
- MCP Client: Connector speaking protocol
- MCP Server: Exposes resources, prompts, tools

Sandboxing (E2B, Firecracker):
- Ephemeral microVMs spun up in milliseconds
- No network access to host infrastructure
- Execute code, return results, destroy sandbox

Tool Validation:
- OpenAPI schemas for all tools
- Pre-execution validation middleware
- Self-healing: Feed errors back to agent for retry"""},
            {"role_type": "assistant", "content": """**Layer 6 - Guardrails Layer:**

Input Guards:
- Prompt injection detection (Rebuff)
- PII redaction (Microsoft Presidio)
- Input length limits

Execution Guards:
- Rate limiting (Redis)
- Policy enforcement (OPA)
- Cost tracking per session

Output Guards:
- Hallucination detection (LLM-as-Judge)
- Topic filtering
- Competitor mention blocking

Circuit Breaker:
- Max 3 consecutive failures
- Cost limit per session ($5)
- Auto-escalate to human operator"""},
            {"role_type": "assistant", "content": """**Layer 7 - Observability Layer:**

Distributed Tracing:
- OpenTelemetry for all spans
- Arize Phoenix or LangSmith for visualization
- Trace: User → Router → LLM → Tool → Response

Evaluations:
- Offline: Golden Dataset with known answers
- Online: LLM-as-Judge sampling
- Metrics: Faithfulness, Relevance, Context Precision

Cost Governance:
- Token tracking per session
- Budget caps per tenant
- Alerts on anomalous spending

Infrastructure:
- Serverless for simple endpoints
- Long-running containers for stateful agents"""},
        ]
    },
]


async def ingest_agentic_framework():
    """Ingest agentic framework knowledge into Azure Zep."""
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Health check
        try:
            r = await client.get(f'{ZEP_URL}/healthz')
            logger.info(f"🏥 Zep health check: {r.status_code}")
            if r.status_code != 200:
                logger.error(f"Zep unhealthy: {r.text}")
                return
        except Exception as e:
            logger.error(f"Cannot reach Zep at {ZEP_URL}: {e}")
            return
        
        # Ensure user exists
        try:
            r = await client.post(f'{ZEP_URL}/api/v1/users', json={'user_id': 'user-derek', 'metadata': {'name': 'Derek'}})
            logger.info(f"👤 User creation: {r.status_code}")
        except Exception as e:
            logger.info(f"User may exist: {e}")
        
        logger.info("\n" + "=" * 70)
        logger.info("INGESTING AGENTIC FRAMEWORK TO AZURE ZEP")
        logger.info("=" * 70)
        
        success = 0
        failed = 0
        
        for ep in AGENTIC_FRAMEWORK_SESSIONS:
            session_id = ep['session_id']
            logger.info(f"\n📝 Session: {session_id}")
            logger.info(f"   Summary: {ep['metadata']['summary'][:60]}...")
            logger.info(f"   Topics: {ep['metadata']['topics']}")
            
            # Create or update session
            try:
                # Try POST first
                r = await client.post(f'{ZEP_URL}/api/v1/sessions', json={
                    'session_id': session_id,
                    'user_id': ep['user_id'],
                    'metadata': ep['metadata']
                })
                
                if r.status_code in [200, 201]:
                    logger.info(f"   ✅ Session created: {r.status_code}")
                elif r.status_code == 400:
                    # Session exists, update metadata with PATCH
                    logger.info(f"   ℹ️  Session exists, updating metadata...")
                    r = await client.patch(f'{ZEP_URL}/api/v1/sessions/{session_id}', json={
                        'metadata': ep['metadata'],
                        'user_id': ep['user_id']
                    })
                    if r.status_code == 200:
                        logger.info(f"   ✅ Metadata updated: {r.status_code}")
                    else:
                        logger.warning(f"   ⚠️ Metadata update failed: {r.status_code} - {r.text[:100]}")
                else:
                    logger.warning(f"   ⚠️ Session status: {r.status_code} - {r.text[:100]}")
            except Exception as e:
                logger.error(f"   ❌ Session error: {e}")
            
            # Add messages
            try:
                r = await client.post(f'{ZEP_URL}/api/v1/sessions/{session_id}/memory', json={
                    'messages': ep['messages']
                })
                if r.status_code == 200:
                    logger.info(f"   ✅ Added {len(ep['messages'])} messages")
                    success += 1
                else:
                    logger.error(f"   ❌ Memory error: {r.status_code} - {r.text[:200]}")
                    failed += 1
            except Exception as e:
                logger.error(f"   ❌ Memory error: {e}")
                failed += 1
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ AGENTIC FRAMEWORK INGESTION COMPLETE")
        logger.info("=" * 70)
        logger.info(f"   ✅ Sessions ingested: {success}")
        logger.info(f"   ❌ Failed: {failed}")
        logger.info(f"   📝 Total messages: {sum(len(ep['messages']) for ep in AGENTIC_FRAMEWORK_SESSIONS)}")
        logger.info("\nThe agents now know:")
        logger.info("   • 7-Layer Production-Grade Agentic System Framework")
        logger.info("   • Current maturity: 2.71/5.0")
        logger.info("   • Critical gap: Layer 6 Guardrails (0.8/5.0)")
        logger.info("   • 16-week roadmap to full maturity")
        logger.info("   • Implementation patterns for all layers")
        logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(ingest_agentic_framework())
