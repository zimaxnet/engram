# Engram Pricing & Features Research

## Document Information

- **Prepared by**: Antigravity (research), Elena Vasquez (GTM Lead)
- **Date**: January 3, 2026
- **Status**: DRAFT - For Discussion

---

## Executive Summary

This document outlines the proposed pricing tiers and feature breakdown for Engram as a commercial product. Pricing is based on competitive research of comparable AI infrastructure platforms.

---

## Our Cost Structure (Infrastructure)

Before setting customer pricing, we need to understand our own costs:

### Memory Layer (Zep)

| Option | Cost | Capacity |
|--------|------|----------|
| **Zep OSS** (current) | $0 | Deprecated, limited features |
| **Zep Cloud Free** | $0/mo | 1,000 episodes/mo |
| **Zep Cloud Flex** | $25/mo | 20,000 episodes/mo |
| **Zep Cloud Enterprise** | Custom | Unlimited, SOC2, HIPAA |

> **Recommendation**: Start with Flex ($25/mo), upgrade when we hit 10k documents.

### Workflow Engine (Temporal)

| Option | Cost | Notes |
|--------|------|-------|
| **Temporal OSS** (current) | $0 | Self-hosted on Azure Container Apps |
| **Temporal Cloud Essentials** | $100/mo min | 5 mil actions included |
| **Temporal Cloud Business** | $500/mo min | SSO, 2.5 mil actions |

> **Current**: Self-hosted OSS at $0 + Azure compute (~$50/mo).

### LLM APIs

| Provider | Model | Input | Output |
|----------|-------|-------|--------|
| Azure OpenAI | GPT-4o | $5/1M tokens | $15/1M tokens |
| Azure OpenAI | GPT-4 Turbo | $15/1M tokens | $45/1M tokens |
| Anthropic | Claude 3.5 Sonnet | $3/1M tokens | $15/1M tokens |
| Google | Gemini 1.5 Pro | $1.25/1M tokens | $5/1M tokens |

> **Cost per conversation**: ~$0.02-0.10 depending on length.

### Azure Infrastructure

| Service | Monthly Estimate |
|---------|------------------|
| Container Apps (API + Worker) | ~$80 |
| PostgreSQL Flexible | ~$50 |
| Static Web Apps | ~$10 |
| Key Vault, Storage | ~$10 |
| **Total** | ~**$150/mo** |

---

## Competitive Landscape

### Mem0 (AI Agent Memory)

| Tier | Price | Features |
|------|-------|----------|
| **Hobby** | Free | 10k memories, 1k retrieval/mo |
| **Pro** | ~$333/mo ($1000 value/3mo) | Unlimited memories, 10k retrieval/mo |
| **Enterprise** | Custom | Unlimited, SSO, on-prem, SLA |

### LangSmith (LangChain)

| Tier | Price | Features |
|------|-------|----------|
| **Developer** | Free | 5k traces/mo |
| **Plus** | $39/seat/mo | 50k traces, 14-day retention |
| **Enterprise** | Custom | Unlimited, SOC2, SSO |

### Dust.tt (AI Agent Platform)

| Tier | Price | Features |
|------|-------|----------|
| **Free** | $0 | Limited agents |
| **Pro** | $29/user/mo | Full features |
| **Enterprise** | Custom | SSO, advanced security |

---

## Proposed Engram Pricing Tiers

### Tier 1: Developer (Free)

**Target**: Individual developers, POC projects

| Feature | Included |
|---------|----------|
| AI Agents | 2 (Elena, Marcus) |
| Memory Storage | 1,000 episodes/mo |
| Conversations | 100/mo |
| Workflows | Basic |
| Support | Community (Discord/GitHub) |

**Our Cost**: ~$0 (OSS stack)

---

### Tier 2: Team ($49/mo)

**Target**: Startups, small teams

| Feature | Included |
|---------|----------|
| AI Agents | Unlimited |
| Memory Storage | 10,000 episodes/mo |
| Conversations | 1,000/mo |
| Workflows | Full Temporal |
| Document Ingestion | 500 docs/mo |
| Voice | 60 min/mo |
| Support | Email (48hr SLA) |
| Users | Up to 5 |

**Our Cost**: ~$50/mo (Zep Flex + shared infra)  
**Margin**: ~$0 (loss leader to build user base)

---

### Tier 3: Business ($199/mo)

**Target**: Growing companies, production use

| Feature | Included |
|---------|----------|
| AI Agents | Unlimited + Custom Agents |
| Memory Storage | 50,000 episodes/mo |
| Conversations | Unlimited |
| Workflows | Full Temporal + Priority Queue |
| Document Ingestion | 2,500 docs/mo |
| Voice | 300 min/mo |
| Knowledge Graph | Full access |
| Analytics | Dashboard + Export |
| Support | Email (24hr SLA) |
| Users | Up to 25 |

**Our Cost**: ~$150/mo  
**Margin**: ~$50/mo (25%)

---

### Tier 4: Enterprise (Custom)

**Target**: Fortune 500, regulated industries

| Feature | Included |
|---------|----------|
| Everything in Business | ✅ |
| Dedicated Instance | Optional |
| SSO (SAML/OIDC) | ✅ |
| SOC2 Compliance | ✅ |
| HIPAA BAA | Available |
| Custom Integrations | ✅ |
| SLA | 99.9% uptime |
| Support | Dedicated CSM, Slack |
| Users | Unlimited |

**Starting at**: $2,000/mo  
**Our Cost**: ~$500-1000/mo (dedicated resources)  
**Margin**: 50-75%

---

## Feature Matrix

| Feature | Developer | Team | Business | Enterprise |
|---------|-----------|------|----------|------------|
| **Agents** | 2 | Unlimited | Unlimited + Custom | Unlimited + Custom |
| **Episodes/mo** | 1,000 | 10,000 | 50,000 | Unlimited |
| **Conversations** | 100 | 1,000 | Unlimited | Unlimited |
| **Voice** | ❌ | 60 min | 300 min | Unlimited |
| **Document Ingest** | 50 | 500 | 2,500 | Unlimited |
| **Knowledge Graph** | Basic | Basic | Full | Full |
| **Custom Agents** | ❌ | ❌ | ✅ | ✅ |
| **API Access** | Read-only | Full | Full | Full |
| **SSO** | ❌ | ❌ | ❌ | ✅ |
| **SLA** | ❌ | ❌ | Best effort | 99.9% |
| **Support** | Community | Email 48hr | Email 24hr | Dedicated |

---

## Add-Ons (À La Carte)

| Add-On | Price | Notes |
|--------|-------|-------|
| Additional voices | $10/30 min | Beyond tier limit |
| Additional documents | $20/500 docs | Bulk ingestion |
| Additional users | $15/user/mo | Team/Business only |
| Priority Support | $100/mo | 4hr response SLA |
| Custom Agent Development | $2,000 one-time | We build it for you |
| White-label | $500/mo | Remove Engram branding |

---

## Pricing Strategy Rationale

### Why These Price Points

1. **Free tier** builds developer community and word-of-mouth
2. **$49/mo** undercuts LangSmith Plus ($39/seat) on per-team basis
3. **$199/mo** aligns with Dust.tt Pro x 7 users, better value
4. **Enterprise** follows standard 10x uplift from Business

### Value Proposition

| Competitor | What They Offer | What We Offer Better |
|------------|-----------------|----------------------|
| Mem0 | Memory only | Memory + Agents + Voice + Workflows |
| LangSmith | Observability | Full agent platform |
| Dust.tt | Agents | Multi-agent + Durable workflows |
| Custom RAG | DIY | Turnkey, managed |

---

## Revenue Projections (Year 1)

| Quarter | Free | Team | Business | Enterprise | MRR |
|---------|------|------|----------|------------|-----|
| Q1 | 100 | 5 | 2 | 0 | $643 |
| Q2 | 300 | 15 | 5 | 1 | $3,730 |
| Q3 | 800 | 40 | 15 | 3 | $11,935 |
| Q4 | 2000 | 100 | 40 | 8 | $31,860 |

**Year 1 ARR Target**: ~$380k

---

## Immediate Next Steps

1. [ ] **Derek**: Approve pricing tiers and feature matrix
2. [ ] **Elena**: Create landing page copy for each tier
3. [ ] **Marcus**: Set up Stripe billing with these tiers
4. [ ] **Dev**: Implement usage metering (episodes, conversations, voice minutes)
5. [ ] **Legal**: Terms of Service and Privacy Policy for commercial use

---

## Open Questions for Derek

1. **Free tier limits**: Are 100 conversations/mo too generous or too restrictive?
2. **Voice pricing**: Should voice be separate add-on or bundled?
3. **Enterprise starting price**: $2,000/mo feel right for Fortune 500?
4. **Custom agent development**: Should we offer this as a service?

---

*This document will be refined based on customer feedback and market response.*
