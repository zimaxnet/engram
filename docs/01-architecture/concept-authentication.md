---
layout: default
title: "Authentication & Security Architecture"
parent: "Architecture"
---

# Authentication & Security Architecture

## Overview

Engram implements a **"Defense in Depth"** security architecture for its API. This approach prioritizes **Application Layer** security over broad "Platform Layer" interceptors to ensure compatibility with modern Single Page Applications (SPAs) and standard web protocols like CORS.

## Core Components

1. **Identity Provider (IdP):**
    - **Azure Entra External ID (CIAM):** Manages user identities (Microsoft, Google, etc.).
    - **MSAL (Frontend):** Handles login flows and acquires Access Tokens.

2. **Transport Layer Security:**
    - **HTTPS/TLS 1.3:** Enforced for all traffic (`engram.work` and `api.engram.work`).

3. **Application Layer Security (The "Brain"):**
    - **Bearer Token Validation:** The backend code (`AuthMiddleware`) validates the cryptographic signature, issuer, and audience of every Bearer Token.
    - **Fine-Grained Access Control:** The application decides *per request* whether to allow it.
        - `OPTIONS` (CORS Preflight): **Allowed** (No token required).
        - `GET/POST` (Data): **Denied** (401 Unauthorized) if no valid token is present.

## Architecture Decision: Disabling Azure "Easy Auth"

### The Problem

Azure Container Apps provides a feature called "Authentication and Authorization" (often called "Easy Auth" or "Platform Auth"). This feature acts as a proxy *in front* of the application.

If enabled, it enforces a binary rule: **"No Token? Redirect to Login."**

This breaks the standard CORS flow for SPAs:

1. Browser sends `OPTIONS` request (Preflight) to check if cross-origin access is allowed.
2. **`OPTIONS` requests do not carry credentials/tokens** (by W3C standard).
3. Azure "Easy Auth" sees no token and returns `302 Found` (Redirect to Login).
4. Browser receives `302` instead of `200 OK`, fails the Preflight check, and blocks the request.

### The Solution

We explicitly **DISABLE** the Platform Auth ("Easy Auth") for the Backend API Container.

```bicep
// infra/modules/backend-aca.bicep
platform: {
  enabled: false // Logic moved to Application Layer
}
```

### Why This Is Secure

Disabling the *platform interceptor* does **NOT** disable authentication. It simply moves the responsibility to the **Application Layer** (`AuthMiddleware`), which is smarter:

- It **allows** unauthenticated `OPTIONS` requests (essential for CORS).
- It **rejects** unauthenticated `GET/POST` requests with `401 Unauthorized` (Secure).

This configuration provides a **secure and compliant** API architecture that works seamlessly with modern web frontends.
