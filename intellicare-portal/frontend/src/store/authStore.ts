import { create } from 'zustand';

export interface TokenResponse {
    access_token: string;
    refresh_token: string;
    expires_in: number;
}

export function parseJwt(token: string) {
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(window.atob(base64).split('').map(function (c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));
        return JSON.parse(jsonPayload);
    } catch (e) {
        return {};
    }
}

interface AuthState {
    accessToken: string | null;
    refreshToken: string | null;
    user: { sub: string; name: string; email: string; preferred_username: string } | null;
    roles: string[];
    tenantId: string | null;
    expiry: number | null;
    setTokens: (data: TokenResponse) => void;
    clear: () => void;
}

// Memory-only storage for access_token to prevent XSS. 
// Refresh token goes to sessionStorage to survive F5 but not new tabs.
export const useAuthStore = create<AuthState>((set) => ({
    accessToken: null,
    refreshToken: null,
    user: null,
    roles: [],
    tenantId: null,
    expiry: null,

    setTokens: (data: TokenResponse) => {
        const payload = parseJwt(data.access_token);
        set({
            accessToken: data.access_token,
            refreshToken: data.refresh_token,
            user: {
                sub: payload.sub,
                name: payload.name || payload.given_name || payload.preferred_username,
                email: payload.email,
                preferred_username: payload.preferred_username
            },
            roles: payload.realm_roles ?? [],
            tenantId: payload.tenant_id ?? null,
            expiry: Date.now() + (data.expires_in * 1000) - 5000, // 5s buffer
        });
        sessionStorage.setItem("refresh_token", data.refresh_token);
    },

    clear: () => {
        sessionStorage.removeItem("refresh_token");
        set({
            accessToken: null,
            refreshToken: null,
            user: null,
            roles: [],
            tenantId: null,
            expiry: null
        });
    },
}));
