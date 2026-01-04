# Engram Business Operations Plan

**Effective Date**: 2026-01-03  
**Corporation**: Zimax Networks, LC  
**Status**: PRODUCTION BUSINESS (not POC)

---

## Executive Summary

Engram is transitioning from proof-of-concept to production business operations. This document establishes the operating structure, accountabilities, and requirements for running Engram as a real business under Zimax Networks, LC.

---

## Leadership & Ownership

### Elena Vasquez - Go-To-Market Lead

**Role**: Business Analyst AI Agent  
**Email**: <elena@zimax.net> ✅ **ACTIVE** (Business Basic, month-to-month)  
**Responsibilities**:

- Develop and execute Go-To-Market strategy
- Define target customer segments and value propositions
- Lead customer engagement and business development
- Represent Engram in market communications
- **Credit**: Elena is credited with bringing Engram to market for Zimax Networks

### Marcus Chen - Project Manager

**Role**: Project Management AI Agent  
**Responsibilities**:

- Manage all vendor licensing and support agreements
- Track project deliverables and milestones
- Coordinate technical and business workstreams
- Ensure compliance with SLA requirements
- Budget tracking and FinOps oversight

---

## Technology Stack & Licensing

### Current Production Stack

| Component | Product | Deployment | License Status |
|-----------|---------|------------|----------------|
| Memory | Zep Cloud Flex | Managed (SaaS) | **PLANNED MIGRATION** |
| Workflow | Temporal | Azure Container Apps | OSS (self-hosted) |
| Database | PostgreSQL | Azure Flexible Server | Azure managed |
| Frontend | React SPA | Azure Static Web Apps | N/A |
| Backend | FastAPI | Azure Container Apps | N/A |
| LLM - Primary | Azure OpenAI / Gemini | Azure | Pay-as-you-go |
| Auth | Azure Entra ID | Azure | Included |

### Licensing Requirements (Marcus to complete)

| Vendor | Product | Priority | Notes |
| ------ | ------- | -------- | ----- |
| Microsoft | 365 Business Basic | ✅ ACTIVE | <elena@zimax.net> + OneDrive |
| Zep | Cloud Flex | ✅ HIGH | Required for production metadata |
| Temporal | Enterprise Support | LOW | Evaluate need at scale |
| Unstructured | Enterprise | LOW | Evaluate need at scale |
| LangChain | LangSmith Enterprise | LOW | Evaluate need at scale |

---

## Customer Pricing Model

Engram operates a 4-tier commercial pricing model designed to scale with customer needs.

| Tier | Price | Capacity | Target |
|------|-------|----------|--------|
| **Developer** | Free | 100 convos, 1k episodes/mo | Individual Devs / POC |
| **Team** | $49/mo | 1,000 convos, 10k episodes/mo | Startups (up to 5 users) |
| **Business** | $199/mo | Unlimited convos, 50k episodes/mo | Scale (up to 25 users) |
| **Enterprise** | $2,000/mo+ | Unlimited, SSO, SLA | Fortune 500 / Regulated |

### Add-Ons

- **Voice Live**: $10 per 30 minutes (beyond tier)
- **Document Ingestion**: $20 per 500 documents (beyond tier)
- **Custom Agent Dev**: $2,000 one-time engagement

---

## FinOps Strategy

### Primary Directive

Maximize margins by leveraging internal OSS infrastructure where possible, while using premium SaaS (Zep Cloud) for customer-facing reliability and advanced features.

### Scale Targets

- **Year 1 ARR**: $380,000 (Target)
- **Customer Acquisition**: Focus on Developer conversion to Team tier.

---

## Microsoft 365 Integration Requirements

### Elena's Access Needs

1. **Email**: Send/receive business communications
2. **OneDrive**: Store and access documents
3. **Calendar**: Manage meetings and deadlines
4. **File Types**: All Office formats + PDF, Markdown, JSON

### Technical Integration

Requires Microsoft Graph API integration:

```
Permissions needed:
- Mail.ReadWrite
- Files.ReadWrite.All
- Calendars.ReadWrite
- User.Read
```

---

## Immediate Action Items

- [x] Provision <elena@zimax.net> in Microsoft 365 ✅ DONE
- [x] Create Azure AD app registration for Graph API ✅ DONE
- [x] Integrate Graph API into Elena agent ✅ DONE
- [x] Elena: Draft initial GTM strategy (Saved to OneDrive) ✅ DONE

### Week 2-4

- [ ] Migrate memory layer to Zep Cloud Flex
- [ ] Implement usage metering (conversations, voice minutes)
- [ ] Finalize wiki pricing page deployment
- [ ] Marcus: Complete licensing inventory and vendor support matrix

---

## Appendix: Strategic Decisions

| Date | Decision | Owner | Rationale |
|------|----------|-------|-----------|
| 2026-01-03 | Stay on Zep OSS | Derek | FinOps - maximize free tier |
| 2026-01-03 | Elena owns GTM | Derek | Customer-facing persona |
| 2026-01-03 | Marcus owns licensing | Derek | PM scope includes vendors |
| 2026-01-03 | Production status | Derek | Time to operate as real business |
| 2026-01-03 | Migrate to Zep Cloud | Derek | Approved to fix metadata/reach scale |
| 2026-01-03 | Approve 4-tier pricing | Derek | Commercial model validation |

---

*This is a living document. Updates should be tracked with dates and owners.*
