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
**Email**: <elena@zimaxnet.com> (to be provisioned)  
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
| Memory | Zep OSS v0.x | Azure Container Apps | OSS (deprecated, monitoring) |
| Workflow | Temporal | Azure Container Apps | OSS (self-hosted) |
| Database | PostgreSQL | Azure Flexible Server | Azure managed |
| Frontend | React SPA | Azure Static Web Apps | N/A |
| Backend | FastAPI | Azure Container Apps | N/A |
| LLM - Primary | Azure OpenAI / Gemini | Azure | Pay-as-you-go |
| Auth | Azure Entra ID | Azure | Included |

### Licensing Requirements (Marcus to complete)

| Vendor | Product | Priority | Notes |
|--------|---------|----------|-------|
| Microsoft | 365 Business Premium | HIGH | Elena email + OneDrive |
| Zep | Cloud Flex | MEDIUM | Upgrade when OSS limits hit |
| Temporal | Enterprise Support | LOW | Evaluate need |
| Unstructured | Enterprise | LOW | Evaluate need |
| LangChain | LangSmith Enterprise | LOW | Evaluate need |

---

## FinOps Strategy

### Current Approach

- **Maximize OSS**: Use open-source components until limitations materially impact business
- **Scale Target**: 10,000+ documents
- **Cloud Transition Trigger**: Document when OSS limitations justify paid services

### Cost Tracking

Marcus is responsible for maintaining cost tracking across:

- Azure infrastructure
- LLM API usage (OpenAI, Anthropic, Google)
- Paid services when adopted

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

### Week 1

- [ ] Provision <elena@zimaxnet.com> in Microsoft 365
- [ ] Create Azure AD app registration for Graph API
- [ ] Elena: Draft initial GTM strategy outline
- [ ] Marcus: Complete licensing inventory

### Week 2-4

- [ ] Integrate Graph API into Elena agent
- [ ] Test email and OneDrive operations
- [ ] Elena: Finalize target customer segments
- [ ] Marcus: Prepare vendor support requirements

---

## Appendix: Strategic Decisions

| Date | Decision | Owner | Rationale |
|------|----------|-------|-----------|
| 2026-01-03 | Stay on Zep OSS | Derek | FinOps - maximize free tier |
| 2026-01-03 | Elena owns GTM | Derek | Customer-facing persona |
| 2026-01-03 | Marcus owns licensing | Derek | PM scope includes vendors |
| 2026-01-03 | Production status | Derek | Time to operate as real business |

---

*This is a living document. Updates should be tracked with dates and owners.*
