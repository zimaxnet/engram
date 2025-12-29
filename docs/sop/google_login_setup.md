# Standard Operating Procedure: Google Login Federation Setup

This guide details the steps to configure Google as an Identity Provider (IdP) for Microsoft Entra External ID (CIAM), enabling users to sign in to Engram with their Google accounts.

## Prerequisites

- Access to [Google Cloud Console](https://console.cloud.google.com/)
- Access to [Microsoft Entra Admin Center](https://entra.microsoft.com/)
- Admin privileges in both tenants

## Phase 1: Google Cloud Console Configuration

1. **Create Project**:
    - Go to **Google Cloud Console**.
    - Create a new project named `Engram Auth` (or similar).

2. **Configure OAuth Consent Screen**:
    - Navigate to **APIs & Services > OAuth consent screen**.
    - Select **External** user type.
    - Fill in App Information:
        - **App Name**: Engram
        - **User Support Email**: [Your Email]
    - **Authorized Domains**: Add `ciamlogin.com` and `microsoftonline.com`.
    - **Developer Contact Information**: [Your Email].
    - Click **Save and Continue**.

3. **Create OAuth Credentials**:
    - Navigate to **APIs & Services > Credentials**.
    - Click **+ CREATE CREDENTIALS** > **OAuth client ID**.
    - **Application Type**: Web application.
    - **Name**: `Entra External ID`.
    - **Authorized Redirect URIs**:
        - You need the specific URI for your Entra tenant.
        - Format: `https://[your-tenant-subdomain].ciamlogin.com/[your-tenant-id]/oauth2/authresp`
        - Example: `https://engramai.ciamlogin.com/engramai.onmicrosoft.com/oauth2/authresp`
    - Click **Create**.

4. **Save Credentials**:
    - Copy the **Client ID** and **Client Secret**. You will need these for Entra.

## Phase 2: Entra External ID Configuration

1. **Add Identity Provider**:
    - Go to **Entra Admin Center**.
    - Navigate to **External Identities > All identity providers**.
    - Click **+ Google**.

2. **Configure Google IdP**:
    - **Client ID**: Paste the Google Client ID.
    - **Client Secret**: Paste the Google Client Secret.
    - Click **Save**.

3. **Enable in User Flow**:
    - Navigate to **External Identities > User flows**.
    - Select your active user flow (e.g., `B2C_1_SignUpSignIn` or default).
    - Click **Identity providers**.
    - Check the box for **Google**.
    - Click **Save**.

## Phase 3: Verification

1. **Frontend Test**:
    - Restart the frontend application.
    - Click "Sign In".
    - You should now see "Sign in with Google" as an option on the Microsoft login page.

2. **Backend Validation (Automated)**:
    - The backend `EntraIDAuth` middleware automatically handles tokens issued via Google federation.
    - The `iss` (issuer) claim will remain the Entra External ID issuer (`https://[domain].ciamlogin.com/...`), so no backend code changes are needed.
    - The `idp` (identity provider) claim in the token will indicate `google.com`.

## Troubleshooting

- **"Redirect URI mismatch"**: Ensure the URL in Google Cloud Console matches *exactly* what Entra expects.
- **"Access blocked: App has not completed the Google verification process"**: For testing, add your specific Google account as a "Test User" in the Google OAuth Consent Screen settings.
