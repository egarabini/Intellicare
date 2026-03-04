import pytest
from httpx import AsyncClient
from uuid import uuid4

@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    response = await async_client.get("/api/v1/gestor/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_create_user(async_client: AsyncClient):
    payload = {
        "nome": "Dr. House",
        "email": "house@hospital.com",
        "cargo": "Diagnostician"
    }
    response = await async_client.post("/api/v1/gestor/users", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "house@hospital.com"
    assert "id" in data

@pytest.mark.asyncio
async def test_list_users(async_client: AsyncClient):
    # Insere 2 users
    await async_client.post("/api/v1/gestor/users", json={"nome": "A", "email": "a@a.com"})
    await async_client.post("/api/v1/gestor/users", json={"nome": "B", "email": "b@b.com"})
    
    response = await async_client.get("/api/v1/gestor/users")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert len(data["users"]) >= 2
