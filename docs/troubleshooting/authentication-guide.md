# Engram Authentication Troubleshooting Guide

## Overview

This document captures the troubleshooting steps and resolutions encountered during the implementation of the Unified Login Modal and Google Federation (CIAM).

## Common Issues & Solutions

### 1. "We couldn't find an account with this email address"

**Symptom:** User clicks "Continue with Google", is redirected to CIAM, but sees an error instead of the Google login prompt.
**Cause:** Google Identity Provider is not enabled in the User Flow, or the Application is not linked to the User Flow.
**Fix:**

- Go to Azure Portal > External Identities > User Flows.
- Select the flow > **Identity Providers** > Check "Google".
- Select **Applications** > Add the App Registration (`engram-local-frontend`).

### 2. Google Error: `redirect_uri_mismatch`

**Symptom:** Google login screen appears but shows Error 400.
**Cause:** The callback URL from Azure CIAM is not whitelisted in Google Cloud Console.
**Fix:**

- Add `https://<tenant>.ciamlogin.com/<tenant_id>/federation/oauth2` to **Authorized redirect URIs** in Google Cloud Console.

### 3. Azure Error: `AADSTS50011` (Invalid Redirect URI)

**Symptom:** "The redirect URI specified in the request does not match..."
**Cause:** The application (e.g., `https://engram.work` or `localhost`) is sending a Redirect URI not registered in Azure AD.
**Fix:**

- Add the exact URI (e.g., `https://engram.work`) to the App Registration > Authentication > Redirect URIs.

### 4. Flashing Popup / `Cross-Origin-Opener-Policy` Error

**Symptom:** Login modal opens, flashes, and closes immediately. User is not logged in.
**Console Log:** `[error] Cross-Origin-Opener-Policy policy would block the window.closed call.`
**Cause:** Modern browser security features (COOP) block the popup from communicating with the parent window (common in Vite/Localhost).
**Fix:**

- Switch from **Popup** flow to **Redirect** flow in `AuthContext.tsx`.
- Replace `instance.loginPopup(request)` with `instance.loginRedirect(request)`.

### 5. Azure Error: `AADSTS9002326` (Cross-origin token redemption)

**Symptom:** Login fails after redirect.
**Console Log:** `ServerError: invalid_request: AADSTS9002326: Cross-origin token redemption is permitted only for the 'Single-Page Application' client-type.`
**Cause:** The Redirect URIs are registered under the **"Web"** platform in Azure, but the app is a public client (SPA) performing cross-origin requests.
**Fix:**

- Move Redirect URIs from "Web" to **"Single-page application"** platform in the App Registration manifest or "Authentication" blade.

### 6. Post-Login Black Screen

**Symptom:** Authenticated successfully (redirect loop finishes), but the app stays blank or empty.
**Console Log:** `net::ERR_CONNECTION_REFUSED` for `localhost:8082`.
**Cause:** Backend services are not running.
**Fix:**

- Start the backend stack: `docker-compose up -d api worker postgres zep`.

### 7. Token Validation Failed (401) - Issuer Mismatch

**Symptom:** Login seems successful, but API calls return 401. Decoding token shows `iss` with GUID subdomain, Backend expects Name subdomain.
**Cause:** Azure CIAM tokens use the Tenant GUID in the Issuer URL (e.g., `https://6684....ciamlogin.com/...`), but `auth.py` defaulted to constructing it from the Domain Name (`engramai`).
**Fix:**

- Update `AZURE_AD_EXTERNAL_DOMAIN` and `AZURE_AD_TENANT_ID` in `.env` (and Azure Parameters) to use the **Tenant GUID** (`6684...`) instead of the domain name.

### 8. Token Validation Failed (401) - Missing Container Env Vars

**Symptom:** Token is valid, but Backend rejects it. Logs show "Request completed" (401 internally).
**Cause:** `docker-compose.yml` was not passing `AZURE_AD_*` variables to the `api` container. The container used default (empty/wrong) values, causing validation to fail.
**Fix:**

- Add `AZURE_AD_TENANT_ID`, `AZURE_AD_CLIENT_ID`, `AZURE_AD_EXTERNAL_DOMAIN`, etc., to the `environment:` section of the `api` service in `docker-compose.yml`.
