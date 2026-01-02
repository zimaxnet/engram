/**
 * Auth Context for Entra External ID
 * 
 * Provides authentication state and methods throughout the app.
 */

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useMsal, useIsAuthenticated, useAccount } from '@azure/msal-react';
import type { AccountInfo } from '@azure/msal-browser';
import { InteractionStatus, type RedirectRequest } from '@azure/msal-browser';
import { loginRequest, getAccessToken } from './authConfig';

interface AuthContextType {
    isAuthenticated: boolean;
    isLoading: boolean;
    user: AccountInfo | null;
    login: (provider?: 'google' | 'microsoft') => Promise<void>;
    logout: () => Promise<void>;
    signUp: () => Promise<void>;
    getToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextType>({
    isAuthenticated: false,
    isLoading: true,
    user: null,
    login: async () => { },
    logout: async () => { },
    signUp: async () => { },
    getToken: async () => null,
});

export function useAuth() {
    return useContext(AuthContext);
}

interface AuthProviderProps {
    children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
    const { instance, inProgress } = useMsal();
    const isAuthenticated = useIsAuthenticated();
    const account = useAccount();
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        // Loading is done when MSAL is not in any interaction
        if (inProgress === InteractionStatus.None) {
            setIsLoading(false);
        }
    }, [inProgress]);

    const login = useCallback(async (provider?: 'google' | 'microsoft') => {
        try {
            const request: RedirectRequest = { ...loginRequest };

            // Add domain hint for Google if requested
            // For CIAM federation, 'google.com' is often the correct hint
            // WORKAROUND: Azure CIAM has a known bug where it sends 'username' param to Google
            // during silent refresh, which Google rejects. Force select_account to bypass this.
            if (provider === 'google') {
                request.prompt = 'select_account';
                request.extraQueryParameters = {
                    ...request.extraQueryParameters,
                    domain_hint: 'google.com'
                };
            }

            // Use redirect to avoid COOP/Popup blocking issues
            await instance.loginRedirect(request);
        } catch (error) {
            console.error('[Auth] Login failed:', error);
            throw error;
        }
    }, [instance]);

    const logout = useCallback(async () => {
        try {
            await instance.logoutRedirect({
                postLogoutRedirectUri: window.location.origin,
            });
        } catch (error) {
            console.error('[Auth] Logout failed:', error);
            throw error;
        }
    }, [instance]);

    const getToken = useCallback(async () => {
        return getAccessToken();
    }, []);

    const signUp = useCallback(async () => {
        try {
            const request: RedirectRequest = {
                ...loginRequest,
                // Use select_account to avoid issues with Google Federation parameters
                prompt: 'select_account',
            };
            await instance.loginRedirect(request);
        } catch (error) {
            console.error('[Auth] Sign up failed:', error);
            throw error;
        }
    }, [instance]);

    const value: AuthContextType = {
        isAuthenticated,
        isLoading,
        user: account,
        login,
        logout,
        signUp,
        getToken,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}
