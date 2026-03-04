import pytest
import pytest_asyncio
from httpx import AsyncClient

from admin.api.app import app

# Utilizando pytest-asyncio e override de dependências se necessário
# Este é um esqueleto inicial dos testes.
# Em um setup real, criaríamos um banco de testes separado e sobreescreveríamos get_db

@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_create_tenant_invalid_cnpj(async_client):
    payload = {
        "nome": "Hospital Santa Clara",
        "cnpj": "11.111.111/1111-11", # Invalido
        "tipo": "HOSPITAL",
        "plano_id": "professional",
        "modulos": []
    }
    response = await async_client.post("/api/v1/admin/estabelecimentos", json=payload)
    assert response.status_code == 422 # Pydantic validation error

@pytest.mark.asyncio
async def test_list_tenants_empty(async_client):
    # Como não mockamos o banco ainda e ele provavelmeente está vazio
    # num DB recém dropado ou de testes, deve retornar lista vazia
    # ou falhar 500 se não conseguir conectar (vamos mockar depois)
    pass
