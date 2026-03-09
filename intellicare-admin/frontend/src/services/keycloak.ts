import Keycloak from 'keycloak-js';
import { API_CONFIG } from '@config/api';

let keycloakInstance: Keycloak | null = null;

export function getKeycloak(): Keycloak {
  if (!keycloakInstance) {
    keycloakInstance = new Keycloak({
      url: API_CONFIG.keycloakUrl,
      realm: API_CONFIG.keycloakRealm,
      clientId: API_CONFIG.keycloakClientId,
    });
  }
  return keycloakInstance;
}

export async function initKeycloak(): Promise<boolean> {
  const kc = getKeycloak();
  try {
    const authenticated = await kc.init({
      onLoad: 'login-required',
      checkLoginIframe: false,
      pkceMethod: 'S256',
    });
    if (authenticated) {
      // Auto-refresh token before expiry
      setInterval(async () => {
        try {
          await kc.updateToken(30);
        } catch {
          kc.login();
        }
      }, 60_000);
    }
    return authenticated;
  } catch (err) {
    console.error('[Keycloak] Init failed:', err);
    return false;
  }
}

export function getToken(): string | undefined {
  return getKeycloak().token;
}

export function logout(): void {
  getKeycloak().logout({ redirectUri: window.location.origin });
}

export function getUserInfo() {
  const kc = getKeycloak();
  const tokenParsed = kc.tokenParsed as Record<string, unknown> | undefined;
  if (!tokenParsed) return null;

  return {
    id: tokenParsed.sub as string,
    name: (tokenParsed.name ?? tokenParsed.preferred_username ?? '') as string,
    email: (tokenParsed.email ?? '') as string,
    roles: (tokenParsed.realm_access as { roles?: string[] })?.roles ?? [],
    tenantId: (tokenParsed.tenant_id ?? tokenParsed.organization ?? '') as string,
    tenantName: (tokenParsed.tenant_name ?? tokenParsed.organization_name ?? '') as string,
  };
}
