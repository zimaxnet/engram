/**
 * Auth Context for Entra External ID
 * 
 * Provides authentication state and methods throughout the app.
 */

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useMsal, useIsAuthenticated, useAccount } from '@azure/msal-react';
import type { AccountInfo } from '@azure/msal-browser';
import { InteractionStatus, type PopupRequest } from '@azure/msal-browser';
import { loginRequest, getAccessToken } from './authConfig';

interface AuthContextType {
    isAuthenticated: boolean;
    isLoading: boolean;
    user: AccountInfo | null;
    login: (provider?: 'google' | 'microsoft') => Promise<void>;
    logout: () => Promise<void>;
    getToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextType>({
    isAuthenticated: false,
    isLoading: true,
    user: null,
    login: async () => { },
    logout: async () => { },
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
            const request: PopupRequest = { ...loginRequest };

            // Add domain hint for Google if requested
            if (provider === 'google') {
                // specific syntax depends on Entra configuration, but domain_hint is standard for OIDC federation
                request.extraQueryParameters = {
                    ...request.extraQueryParameters,
                    domain_hint: 'google'
                };
            }

            // Use popup for better UX (redirect also works)
            await instance.loginPopup(request);
        } catch (error) {
            console.error('[Auth] Login failed:', error);
            throw error;
        }
    }, [instance]);

    const logout = useCallback(async () => {
        try {
            await instance.logoutPopup({
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

    const value: AuthContextType = {
        isAuthenticated,
        isLoading,
        user: account,
        login,
        logout,
        getToken,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}
