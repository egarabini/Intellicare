

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
        params.append('audience', config.keycloak.clientId);
        params.append('tenant_id', tenantId);

        const keycloakUrl = config.keycloak.url.endsWith('/')
            ? config.keycloak.url
            : `${config.keycloak.url}/`;

        const tokenEndpoint = `${keycloakUrl}realms/${config.keycloak.realm}/protocol/openid-connect/token`;

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
