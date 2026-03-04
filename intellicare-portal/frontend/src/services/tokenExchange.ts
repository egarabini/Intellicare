

/**
 * Performs a Token Exchange directly with Keycloak to swap the current access token
 * for one scoped to a specific tenant.
 */
export async function exchangeTokenForTenant(currentToken: string, tenantId: string): Promise<string> {
    try {
        const params = new URLSearchParams();
        params.append('grant_type', 'urn:ietf:params:oauth:grant-type:token-exchange');
        params.append('subject_token', currentToken);
        params.append('requested_token_type', 'urn:ietf:params:oauth:token-type:access_token');
        params.append('audience', import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'intellicare-portal');
        params.append('tenant_id', tenantId);

        const envUrl = import.meta.env.VITE_KEYCLOAK_URL || 'http://localhost:8080';
        const keycloakUrl = envUrl.endsWith('/')
            ? envUrl
            : `${envUrl}/`;

        const tokenEndpoint = `${keycloakUrl}realms/${import.meta.env.VITE_KEYCLOAK_REALM || 'bemcuidar'}/protocol/openid-connect/token`;

        const response = await fetch(tokenEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: params,
        });

        if (!response.ok) {
            throw new Error(`Token exchange failed with status: ${response.status}`);
        }

        const data = await response.json();
        return data.access_token;
    } catch (error) {
        console.error('Error during token exchange:', error);
        throw error;
    }
}
