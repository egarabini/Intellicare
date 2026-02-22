/**
 * TenantProvider — Contexto React para multi-tenancy.
 * 
 * Gerencia o ciclo de vida do tenant no frontend:
 * 1. Decodifica o JWT para extrair tenants[] e tenant_id
 * 2. Se single-tenant → auto-select + token exchange silencioso
 * 3. Se multi-org sem seleção → mostra TenantSelectorPage
 * 4. Se tenant selecionado → carrega info e disponibiliza via contexto
 */

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { decodeJwt, tokenExchange, getStoredToken, storeToken, type DecodedToken } from '../services/tokenExchange';

// ─── Types ──────────────────────────────────────────────────

export interface TenantInfo {
    tenantId: string;
    tenantName: string;
    tenantLogo?: string;
    modules: string[];
    plan?: string;
}

export interface TenantContextValue {
    /** Info do tenant ativo */
    tenant: TenantInfo | null;
    /** Lista de tenants disponíveis (multi-org) */
    availableTenants: string[];
    /** Se o usuario pertence a múltiplas organizações */
    isMultiOrg: boolean;
    /** Se um tenant está selecionado e carregado */
    isReady: boolean;
    /** Se está mostrando a tela de seleção */
    showSelector: boolean;
    /** Selecionar um tenant (dispara token exchange) */
    selectTenant: (tenantId: string) => Promise<void>;
    /** Trocar de organização (volta para seleção) */
    switchOrg: () => void;
    /** Token decodificado */
    decodedToken: DecodedToken | null;
}

const TenantContext = createContext<TenantContextValue>({
    tenant: null,
    availableTenants: [],
    isMultiOrg: false,
    isReady: false,
    showSelector: false,
    selectTenant: async () => { },
    switchOrg: () => { },
    decodedToken: null,
});

// ─── Hook ───────────────────────────────────────────────────

export function useTenant(): TenantContextValue {
    return useContext(TenantContext);
}

// ─── Provider ───────────────────────────────────────────────

interface TenantProviderProps {
    children: ReactNode;
    /** Se false, ignora multi-tenancy (modo demo/dev) */
    enabled?: boolean;
}

export function TenantProvider({ children, enabled = true }: TenantProviderProps) {
    const [tenant, setTenant] = useState<TenantInfo | null>(null);
    const [availableTenants, setAvailableTenants] = useState<string[]>([]);
    const [showSelector, setShowSelector] = useState(false);
    const [isReady, setIsReady] = useState(!enabled); // Pronto se desabilitado
    const [decodedToken, setDecodedToken] = useState<DecodedToken | null>(null);

    // Carregar info de tenant a partir do ID
    const loadTenantInfo = useCallback(async (tenantId: string): Promise<void> => {
        // TODO: Buscar do backend (intellicare-admin /api/v1/tenants/{id})
        // Por agora, gera info baseada no ID
        const info: TenantInfo = {
            tenantId,
            tenantName: tenantId
                .replace(/_/g, ' ')
                .replace(/\b\w/g, (c) => c.toUpperCase()),
            modules: ['oswaldo', 'florence', 'zilda', 'wanda'], // Default
        };
        setTenant(info);
        setIsReady(true);
        setShowSelector(false);
    }, []);

    // Selecionar tenant (multi-org)
    const selectTenant = useCallback(async (tenantId: string): Promise<void> => {
        const token = getStoredToken();
        if (!token) return;

        try {
            // Token exchange com Keycloak
            const result = await tokenExchange(token, tenantId);
            storeToken(result.access_token);
            setDecodedToken(decodeJwt(result.access_token));
            await loadTenantInfo(tenantId);
        } catch (error) {
            console.error('Token exchange failed:', error);
            // Fallback: usar o tenant sem exchange (modo dev)
            await loadTenantInfo(tenantId);
        }
    }, [loadTenantInfo]);

    // Trocar de organização
    const switchOrg = useCallback(() => {
        setTenant(null);
        setIsReady(false);
        setShowSelector(true);
    }, []);

    // Inicialização: analisar token ao montar
    useEffect(() => {
        if (!enabled) return;

        const token = getStoredToken();
        if (!token) {
            // Sem token = modo público (demo)
            setIsReady(true);
            return;
        }

        const decoded = decodeJwt(token);
        setDecodedToken(decoded);

        const tenants = decoded.tenants || [];
        const tenantId = decoded.tenant_id;

        setAvailableTenants(tenants);

        if (tenantId) {
            // Cenário 1: tenant já selecionado
            loadTenantInfo(tenantId);
        } else if (tenants.length === 1) {
            // Cenário 2: auto-select (apenas 1 tenant)
            selectTenant(tenants[0]);
        } else if (tenants.length > 1) {
            // Cenário 3: multi-org — mostrar selector
            setShowSelector(true);
        } else {
            // Cenário 4: sem tenant info (modo público)
            setIsReady(true);
        }
    }, [enabled, loadTenantInfo, selectTenant]);

    const value: TenantContextValue = {
        tenant,
        availableTenants,
        isMultiOrg: availableTenants.length > 1,
        isReady,
        showSelector,
        selectTenant,
        switchOrg,
        decodedToken,
    };

    return (
        <TenantContext.Provider value={value}>
            {children}
        </TenantContext.Provider>
    );
}

export default TenantProvider;
