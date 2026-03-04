import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { decodeToken, getTenantsArray, getTenantId } from '../utils/jwt';
import { exchangeTokenForTenant } from '../services/tokenExchange';
import { useAuthStore } from '../store/authStore';
import api from '../services/api';

export interface TenantInfo {
    tenantId: string;
    name: string;
    logoUrl?: string;
    primaryColor: string;
    secondaryColor: string;
    activeModules: string[];
}

interface TenantContextType {
    tenantInfo: TenantInfo | null;
    isLoading: boolean;
    error: string | null;
    changeTenant: (tenantId: string) => Promise<void>;
}

const TenantContext = createContext<TenantContextType | undefined>(undefined);

export const TenantProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const { token, setToken, logout } = useAuthStore();
    const [tenantInfo, setTenantInfo] = useState<TenantInfo | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showSelector, setShowSelector] = useState(false); // To be implemented via a Provider UI wrapper

    useEffect(() => {
        const initializeTenant = async () => {
            if (!token) {
                setIsLoading(false);
                return;
            }

            setIsLoading(true);
            setError(null);

            try {
                const decoded = decodeToken(token);
                if (!decoded) throw new Error('Invalid token');

                const tenantId = decoded.tenant_id;
                const availableTenants = decoded.tenants || [];

                // Scenario 1: User has no tenants configured
                if (!tenantId && availableTenants.length === 0) {
                    setError('Nenhuma organização configurada para este usuário.');
                    setIsLoading(false);
                    return;
                }

                // Scenario 2: Multi-tenant, no active selection -> show selector (handled by UI layer)
                if (!tenantId && availableTenants.length > 1) {
                    setShowSelector(true);
                    setIsLoading(false);
                    return;
                }

                // Scenario 3: Only 1 tenant available, but not actively selected in token
                let currentToken = token;
                if (!tenantId && availableTenants.length === 1) {
                    const newToken = await exchangeTokenForTenant(token, availableTenants[0]);
                    setToken(newToken);
                    currentToken = newToken;
                }

                // We have a stable token with a tenant_id, let's load branding & modules
                await fetchTenantProfile(currentToken);

            } catch (err) {
                console.error('Failed to initialize tenant context:', err);
                setError('Falha ao autenticar o ambiente da sua organização.');
            } finally {
                setIsLoading(false);
            }
        };

        initializeTenant();
    }, [token, setToken]);

    const fetchTenantProfile = async (currentToken: string) => {
        try {
            // In a real scenario, this would call /gestor/settings and /admin/tenants/{id}/modules
            // using the axios api instance which will inject the Bearer token automatically

            // Mock for development of UI components (Replace with real API calls soon)
            const mockTenantInfo: TenantInfo = {
                tenantId: getTenantId(currentToken) || 'unknown',
                name: 'Hospital São João',
                primaryColor: '#1E88E5',
                secondaryColor: '#43A047',
                activeModules: ['florence', 'oswaldo', 'gestor', 'admin', 'geralda', 'comunicacao'],
            };

            setTenantInfo(mockTenantInfo);
            applyBranding(mockTenantInfo);

        } catch (e) {
            console.error('Failed to fetch tenant branding:', e);
            // Fallback
        }
    };

    const applyBranding = (info: TenantInfo) => {
        document.documentElement.style.setProperty('--tenant-primary', info.primaryColor);
        document.documentElement.style.setProperty('--tenant-secondary', info.secondaryColor);
    };

    const changeTenant = async (newTenantId: string) => {
        if (!token) return;
        setIsLoading(true);
        try {
            const newToken = await exchangeTokenForTenant(token, newTenantId);
            setToken(newToken);
            // The useEffect will react to the token change and re-fetch everything
        } catch (err) {
            console.error('Failed to change org', err);
            setError('Falha ao trocar de organização.');
            setIsLoading(false);
        }
    };

    return (
        <TenantContext.Provider value={{ tenantInfo, isLoading, error, changeTenant }}>
            {/* We expose a static true UI flag if they need to see the selector. For now we will implement this logic locally in App.tsx */}
            {children}
        </TenantContext.Provider>
    );
};

export const useTenantContext = () => {
    const context = useContext(TenantContext);
    if (context === undefined) {
        throw new Error('useTenantContext must be used within a TenantProvider');
    }
    return context;
};
