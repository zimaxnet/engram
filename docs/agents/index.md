---
layout: default
title: Agent Personas
nav_order: 4
has_children: true
---

# [Home](/) › Agents

# Agent Personas

The Engram platform features specialized AI agent personas designed for enterprise business analysis and project management.

## Meet Our Agents

### Dr. Elena Vasquez - Business Analyst

![Dr. Elena Vasquez Portrait](/assets/images/elena-portrait.png)

**Background**: Ph.D. in Information Systems from MIT, MBA from Stanford. 15 years of experience in management consulting, digital transformation, and academic research.

**Expertise**:

- Requirements Analysis
- Stakeholder Management
- Process Optimization
- Digital Strategy
- Change Management

**Voice**: Jenny Neural (warm, professional)  
**Accent Color**: Cyan (`#00d4ff`)

[Learn More About Elena](elena/persona.md)

### Marcus Chen - Project Manager

![Marcus Chen Portrait](/assets/images/marcus-portrait.png)

**Background**: Certified PMP and PMI-ACP. 12 years of experience managing complex technology programs at Amazon, Salesforce, and high-growth startups.

**Expertise**:

- Program Management
- Agile Transformation
- Risk Management
- Resource Planning
- Executive Communication

**Voice**: Guy Neural (confident, professional)  
**Accent Color**: Purple (`#a855f7`)

[Learn More About Marcus](marcus/persona.md)

### Sage - Visual Storyteller

**Background**: Specialized agent for creating visual content, stories, and diagrams.

**Expertise**:

- Visual Art Generation
- Story Creation
- Diagram Generation
- Visual Content Ingestion

[Learn More About Sage](sage/visual-implementation-report.md)

## Agent Collaboration

Elena and Marcus are designed to work together seamlessly:

| Trigger | From | To | Context Passed |
|---------|------|-----|----------------|
| "plan this project" | Elena | Marcus | Requirements analysis |
| "what are the requirements" | Marcus | Elena | Project scope |
| "estimate timeline" | Elena | Marcus | User stories |
| "analyze stakeholders" | Marcus | Elena | Project constraints |

## Agent Attribution

All agent actions are fully attributable:

- **User ID**: Who invoked the agent
- **Agent ID**: Which agent performed the action
- **Tenant ID**: Enterprise boundary
- **Project**: Project scope

See: [Security Context Architecture](../architecture/context-schema/security-context-enterprise-architecture.md)

---

**Next**: Explore [Architecture](../architecture/) or [Features](../features/).
