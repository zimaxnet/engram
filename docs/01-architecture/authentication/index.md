---
layout: default
title: Authentication & Security
---

# [Home](/) › [Architecture](../) › Authentication & Security

# Authentication & Security Architecture

Engram uses **Azure Entra ID (External ID)** with **Google Federation** for enterprise-grade authentication and security.

## Overview

- **Identity Provider**: Azure Entra ID (CIAM)
- **Social Login**: Google Federation
- **Token Format**: JWT (JSON Web Token)
- **Validation**: Standard JWT validation with dynamic JWKS fetching

## Documentation

- [Authentication Analysis](authentication-analysis.md) - Deep dive into authentication flow
- [Authentication Architecture Evolution](authentication-architecture-evolution.md) - Evolution of auth approach
- [Enterprise Auth Strategy](enterprise-auth-strategy.md) - Production authentication strategy
- [Entra External ID](entra-external-id.md) - Azure CIAM integration guide

## Diagrams

- [Authentication Flow Diagram](diagrams/auth-flow-diagram.json) - Complete authentication flow
- [Security Context Flow Diagram](diagrams/security-context-flow-diagram.json) - SecurityContext flow through systems
- [Authentication Flow Images](diagrams/) - Visual diagrams

## Key Concepts

### Authentication Flow

1. User clicks "Continue with Google"
2. Frontend redirects to Azure CIAM
3. Azure CIAM federates to Google
4. Google authenticates user
5. Azure CIAM issues JWT token
6. Backend validates token (dynamic JWKS fetching)
7. SecurityContext created from token claims

### SecurityContext

**SecurityContext** (Layer 1) is created from JWT token:
- `user_id` from `oid` claim
- `tenant_id` from `tid` claim
- `roles` from Entra ID groups
- `scopes` from token scopes
- `email`, `display_name` from token claims

See: [Security Context Architecture](../context-schema/security-context-enterprise-architecture.md)

### Enterprise Boundaries

SecurityContext enforces:
- **Tenant Isolation**: Contoso Corp users cannot access Fabrikam Corp data
- **Project Scoping**: Users only see projects they have access to
- **Role-Based Access**: ANALYST can read, ADMIN can modify
- **User Attribution**: All actions are attributable to a user

## Troubleshooting

- [Authentication Guide](../../operations/troubleshooting/authentication-guide.md)
- [Token Validation Fix](../../operations/troubleshooting/auth-token-validation-fix.md)
- [CORS Fix](../../operations/troubleshooting/cors-preflight-400-fix.md)

---

**Related**: [Security Context](../context-schema/security-context-enterprise-architecture.md), [Operations](../../operations/)

