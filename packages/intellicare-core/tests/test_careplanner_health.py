import pytest

@pytest.mark.asyncio
async def test_health_adapters_returns_all_channels(client, gestor_token):
    resp = await client.get(
        "/api/v1/careplanner/health/adapters",
        headers={"Authorization": f"Bearer {gestor_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"rocketchat", "whatsapp", "email", "sms"}
    # Em CI todos os adapters estarão degraded — verificar estrutura, não valor
    for v in body.values():
        assert isinstance(v, str)
