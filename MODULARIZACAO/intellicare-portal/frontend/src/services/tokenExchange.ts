/**
 * Token Exchange Service
 * 
 * Handles Keycloak token exchange for multi-org tenant selection.
 * When a user belongs to multiple organizations, this service
 * exchanges the initial JWT for a tenant-scoped JWT.
 */

const KEYCLOAK_URL = import.meta.env.VITE_KEYCLOAK_URL || 'https://keycloak.gsi.srv.br';
const KEYCLOAK_REALM = import.meta.env.VITE_KEYCLOAK_REALM || 'bemcuidar';
const KEYCLOAK_CLIENT_ID = import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'intellicare-portal';

export interface TokenExchangeResult {
    access_token: string;
    refresh_token?: string;
    token_type: string;
    expires_in: number;
}

export interface DecodedToken {
    sub: string;
    preferred_username?: string;
    tenant_id?: string | null;
    tenants?: string[];
    realm_access?: { roles: string[] };
    exp?: number;
}

/**
 * Decode a JWT payload without verification (client-side only).
 * The backend validates the token — this is just for reading claims.
 */
export function decodeJwt(token: string): DecodedToken {
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(
            atob(base64)
                .split('')
                .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
                .join('')
        );
        return JSON.parse(jsonPayload);
    } catch {
        return { sub: '', tenants: [] };
    }
}

/**
 * Exchange the current token for a tenant-scoped token.
 * 
 * Uses Keycloak's Token Exchange flow:
 * - grant_type: urn:ietf:params:oauth:grant-type:token-exchange
 * - subject_token: the current JWT
 * - requested_token_type: access_token
 * - audience: the client itself (with tenant_id as requested scope)
 */
export async function tokenExchange(
    currentToken: string,
    selectedTenantId: string
): Promise<TokenExchangeResult> {
    const tokenUrl = `${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/token`;

    const params = new URLSearchParams({
        grant_type: 'urn:ietf:params:oauth:grant-type:token-exchange',
        client_id: KEYCLOAK_CLIENT_ID,
        subject_token: currentToken,
        requested_token_type: 'urn:ietf:params:oauth:token-type:access_token',
        audience: KEYCLOAK_CLIENT_ID,
        // Custom parameter for the Keycloak SPI to select tenant
        'tenant_id': selectedTenantId,
    });

    const response = await fetch(tokenUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: params.toString(),
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ error: 'unknown' }));
        throw new Error(
            `Token exchange failed: ${error.error_description || error.error || response.statusText}`
        );
    }

    return response.json();
}

/**
 * Get stored token from localStorage.
 */
export function getStoredToken(): string | null {
    return localStorage.getItem('token');
}

/**
 * Store token in localStorage.
 */
export function storeToken(token: string): void {
    localStorage.setItem('token', token);
}

/**
 * Remove stored token.
 */
export function clearToken(): void {
    localStorage.removeItem('token');
}
