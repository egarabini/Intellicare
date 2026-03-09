import { useAuthStore, TokenResponse } from '../store/authStore';

// We should load these from import.meta.env, but falling back to defaults for safety
const KEYCLOAK_URL = import.meta.env.VITE_KEYCLOAK_URL || 'https://auth.intellicare.ia.br';
const REALM = import.meta.env.VITE_KEYCLOAK_REALM || 'bemcuidar';
const CLIENT_ID = import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'intellicare-portal';

// Crypto Helpers for PKCE
function generateCodeVerifier(): string {
    const array = new Uint32Array(56 / 2);
    window.crypto.getRandomValues(array);
    return Array.from(array, (dec) => ('0' + dec.toString(16)).substr(-2)).join('');
}

async function generateCodeChallenge(verifier: string): Promise<string> {
    const data = new TextEncoder().encode(verifier);
    const digest = await window.crypto.subtle.digest('SHA-256', data);
    return btoa(String.fromCharCode.apply(null, Array.from(new Uint8Array(digest))))
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=+$/, '');
}

export async function iniciarLogin(redirectAfter?: string): Promise<void> {
    const verifier = generateCodeVerifier();
    const challenge = await generateCodeChallenge(verifier);

    sessionStorage.setItem("pkce_verifier", verifier);
    if (redirectAfter) {
        sessionStorage.setItem("redirect_after", redirectAfter);
    } else {
        sessionStorage.removeItem("redirect_after");
    }

    const params = new URLSearchParams({
        client_id: CLIENT_ID,
        redirect_uri: `${window.location.origin}/auth/callback`,
        response_type: "code",
        scope: "openid profile email",
        code_challenge: challenge,
        code_challenge_method: "S256",
        state: crypto.randomUUID(),
    });

    window.location.href = `${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/auth?${params.toString()}`;
}

export async function handleCallback(code: string): Promise<void> {
    const verifier = sessionStorage.getItem("pkce_verifier");
    if (!verifier) throw new Error("PKCE verifier not found in session storage.");

    const body = new URLSearchParams({
        grant_type: "authorization_code",
        code,
        redirect_uri: `${window.location.origin}/auth/callback`,
        client_id: CLIENT_ID,
        code_verifier: verifier,
    });

    const resp = await fetch(`${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/token`, {
        method: "POST",
        body,
        headers: { "Content-Type": "application/x-www-form-urlencoded" }
    });

    if (!resp.ok) {
        throw new Error(`Token exchange failed: ${resp.statusText}`);
    }

    const data: TokenResponse = await resp.json();
    useAuthStore.getState().setTokens(data);
    sessionStorage.removeItem("pkce_verifier");
}

export async function refreshToken(): Promise<boolean> {
    const refresh_token = sessionStorage.getItem("refresh_token");
    if (!refresh_token) return false;

    const body = new URLSearchParams({
        grant_type: "refresh_token",
        client_id: CLIENT_ID,
        refresh_token: refresh_token,
    });

    try {
        const resp = await fetch(`${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/token`, {
            method: "POST",
            body,
            headers: { "Content-Type": "application/x-www-form-urlencoded" }
        });

        if (!resp.ok) {
            useAuthStore.getState().clear();
            return false;
        }

        const data: TokenResponse = await resp.json();
        useAuthStore.getState().setTokens(data);
        return true;
    } catch (e) {
        useAuthStore.getState().clear();
        return false;
    }
}

export function logout(): void {
    useAuthStore.getState().clear();
    window.location.href = `${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/logout?client_id=${CLIENT_ID}&post_logout_redirect_uri=${window.location.origin}/login`;
}
