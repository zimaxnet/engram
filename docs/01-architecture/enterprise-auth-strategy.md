---
layout: default
title: "Enterprise Authentication Strategy: From POC to Production"
parent: "Architecture"
---

# Enterprise Authentication Strategy: From POC to Production

You asked how the current solution (disabling Platform Auth + App-level Bypass) correlates to a repeatable enterprise solution. This document outlines the architectural distinction and the path forward.

## Current State: POC / "Soft" Auth

Currently, we are using application-level logic to decide whether to enforce authentication.

- **Mechanism**: `auth.py` checks `AUTH_REQUIRED`. If false, it injects a "POC User" identity.
- **Requirement**: Azure Container Apps Platform Auth ("Easy Auth") must be **Disabled** (or set to Allow Anonymous) so that requests actually reach our `auth.py` logic.
- **Pros**: Rapid development, easy debugging, no external dependencies for local dev.
- **Cons**: Relies on code correctness for security; not suitable for Zero Trust environments.

## Target State: Enterprise / Zero Trust

In a production enterprise solution, we strictly separate **Authentication** (Who are you?) from **Authorization** (What can you do?).

### 1. Identity Gateway (Platform Auth)

Instead of disabling it, we will **Enable** Azure Container Apps Authentication.

- **Role**: Blocks unauthenticated traffic *before* it reaches the container.
- **Config**: Configured to require a valid Entra ID (Azure AD) token.
- **Benefit**: Zero Trust. If a request reaches your code, it is guaranteed to be from a valid identity. Your code never handles "public" traffic.

### 2. Application-Level RBAC

The application no longer "authenticates" users but "authorizes" them based on the token passed by the gateway.

- **Mechanism**: `auth.py` reads the `X-MS-CLIENT-PRINCIPAL` header injected by Azure.
- **Logic**: Maps the Entra ID claims (Groups/Roles) to Engram Roles (Admin, Analyst, etc.).

## The "Repeatable" Solution

To make this a repeatable artifact (Infrastructure-as-Code), the final bicep/terraform templates will:

1. **Enforce Platform Auth**: Set `azureContainerApps/authConfigs` to `enabled: true` with `unauthenticatedClientAction: Return401`.
2. **Configure Entra ID**: Automatically register the App Registration and pass Client ID/Secret to the container environment.
3. **Application Config**: Set `AUTH_REQUIRED=true`.

### Why the "Fix" felt like a workaround

The confusion arose because we had **Platform Auth enabled** (blocking requests) but **Application Auth disabled** (expecting to bypass). They contradicted each other.

- **Workaround (Now)**: Disable Platform Auth → Code handles everything (including bypass).
- **Enterprise (Future)**: Enable Platform Auth → Code handles Authorization only.

## Summary Checklist for Enterprise Transition

- [ ] Enable Azure Container Apps Authentication (Entra ID provider).
- [ ] Update `auth.py` to trust `X-MS-CLIENT-PRINCIPAL` headers (standard pattern for App Service/Container Apps).
- [ ] Set `AUTH_REQUIRED=true`.
- [ ] Remove `_no_auth_dependency` bypass logic from production builds.
