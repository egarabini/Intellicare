const WANDA_URL = import.meta.env.VITE_WANDA_URL || 'http://localhost:8004';

export async function exchangeTokenForTenant(
    token: string,
    tenantId: string
): Promise<string> {
    const resp = await fetch(`${WANDA_URL}/api/v1/token/exchange`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ tenant_id: tenantId }),
    });
    if (!resp.ok) {
        throw new Error(`Token exchange failed: ${resp.status}`);
    }
    const data = await resp.json();
    return data.access_token;
}
