/**
 * MSAL Configuration for Entra External ID
 * 
 * Tenant: engramai.onmicrosoft.com
 * Auth Endpoint: engramai.ciamlogin.com
 */

import type { Configuration } from '@azure/msal-browser';
import { LogLevel, PublicClientApplication } from '@azure/msal-browser';

// Environment variables (set in .env or via Vite)
const TENANT_DOMAIN = import.meta.env.VITE_AZURE_AD_TENANT_DOMAIN || 'engramai';
const TENANT_ID = import.meta.env.VITE_AZURE_AD_TENANT_ID || 'engramai.onmicrosoft.com';
const CLIENT_ID = import.meta.env.VITE_AZURE_AD_CLIENT_ID || '';
const REDIRECT_URI = import.meta.env.VITE_REDIRECT_URI || window.location.origin;

// MSAL Configuration for Entra External ID
export const msalConfig: Configuration = {
    auth: {
        clientId: CLIENT_ID,
        // External ID uses ciamlogin.com authority
        authority: `https://${TENANT_DOMAIN}.ciamlogin.com/${TENANT_ID}`,
        // Alternatively for B2C: `https://${TENANT_DOMAIN}.b2clogin.com/${TENANT_ID}/${POLICY_NAME}`
        redirectUri: REDIRECT_URI,
        postLogoutRedirectUri: REDIRECT_URI,
        // Required for External ID
        knownAuthorities: [`${TENANT_DOMAIN}.ciamlogin.com`],
        navigateToLoginRequestUrl: true,
    },
    cache: {
        cacheLocation: 'localStorage', // or 'sessionStorage'
        storeAuthStateInCookie: false,
    },
    system: {
        loggerOptions: {
            logLevel: import.meta.env.DEV ? LogLevel.Verbose : LogLevel.Error,
            loggerCallback: (level, message, containsPii) => {
                if (containsPii) return;
                switch (level) {
                    case LogLevel.Error:
                        console.error('[MSAL]', message);
                        break;
                    case LogLevel.Warning:
                        console.warn('[MSAL]', message);
                        break;
                    case LogLevel.Info:
                        console.info('[MSAL]', message);
                        break;
                    case LogLevel.Verbose:
                        console.debug('[MSAL]', message);
                        break;
                }
            },
        },
    },
};

// Scopes for API access
export const loginRequest = {
    scopes: ['openid', 'profile', 'email', 'offline_access'],
};

// API scopes (if backend requires specific scopes)
export const apiRequest = {
    scopes: [`api://${CLIENT_ID}/access_as_user`],
};

// Create MSAL instance
export const msalInstance = new PublicClientApplication(msalConfig);

// Initialize MSAL
export async function initializeMsal(): Promise<void> {
    await msalInstance.initialize();

    // Handle redirect after login
    const response = await msalInstance.handleRedirectPromise();
    if (response) {
        console.log('[MSAL] Login redirect handled:', response.account?.username);
    }
}

// Check if user is authenticated
export function isAuthenticated(): boolean {
    const accounts = msalInstance.getAllAccounts();
    return accounts.length > 0;
}

// Get current account
export function getCurrentAccount() {
    const accounts = msalInstance.getAllAccounts();
    return accounts.length > 0 ? accounts[0] : null;
}

// Get access token (with silent fallback)
export async function getAccessToken(): Promise<string | null> {
    const account = getCurrentAccount();
    if (!account) return null;

    try {
        const response = await msalInstance.acquireTokenSilent({
            ...loginRequest,
            account,
        });
        return response.accessToken;
    } catch (error) {
        console.warn('[MSAL] Silent token acquisition failed, will redirect');
        // Fallback to interactive if silent fails
        await msalInstance.acquireTokenRedirect(loginRequest);
        return null;
    }
}
