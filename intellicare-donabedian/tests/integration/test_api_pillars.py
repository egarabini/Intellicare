"""
Testes de integração para endpoints de Pilares.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestPillarsIntegration:
    """Testes de integração para endpoints de Pilares."""
    
    async def test_create_pillar(self, client: AsyncClient):
        """Testa criação de pilar via API."""
        response = await client.post(
            "/api/v1/pillars",
            json={
                "name": "Eficácia",
                "description": "Capacidade de produzir o efeito desejado",
                "display_order": 1
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Eficácia"
        assert data["display_order"] == 1
        assert "id" in data
    
    async def test_list_pillars(self, client: AsyncClient, sample_pillar):
        """Testa listagem de pilares via API."""
        response = await client.get("/api/v1/pillars")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["name"] == sample_pillar.name
    
    async def test_get_pillar(self, client: AsyncClient, sample_pillar):
        """Testa busca de pilar específico via API."""
        response = await client.get(f"/api/v1/pillars/{sample_pillar.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_pillar.id
        assert data["name"] == sample_pillar.name
    
    async def test_update_pillar(self, client: AsyncClient, sample_pillar):
        """Testa atualização de pilar via API."""
        response = await client.put(
            f"/api/v1/pillars/{sample_pillar.id}",
            json={
                "name": "Eficácia Atualizada",
                "description": "Nova descrição",
                "display_order": 2
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Eficácia Atualizada"
        assert data["display_order"] == 2
    
    async def test_delete_pillar(self, client: AsyncClient, sample_pillar):
        """Testa exclusão de pilar via API."""
        response = await client.delete(f"/api/v1/pillars/{sample_pillar.id}")
        
        assert response.status_code == 204
        
        # Verifica que foi deletado
        response = await client.get(f"/api/v1/pillars/{sample_pillar.id}")
        assert response.status_code == 404
    
    async def test_get_pillar_not_found(self, client: AsyncClient):
        """Testa busca de pilar inexistente."""
        response = await client.get("/api/v1/pillars/99999")
        
        assert response.status_code == 404
    
    async def test_create_pillar_validation_error(self, client: AsyncClient):
        """Testa validação ao criar pilar com dados inválidos."""
        response = await client.post(
            "/api/v1/pillars",
            json={
                "name": "",  # Nome vazio
                "description": "Descrição",
                "display_order": 1
            }
        )
        
        assert response.status_code == 422
    
    async def test_list_pillars_with_indicators(self, client: AsyncClient, sample_pillar, sample_indicator_pillar):
        """Testa listagem de pilares com indicadores associados."""
        response = await client.get("/api/v1/pillars")
        
        assert response.status_code == 200
        data = response.json()
        
        # Encontra o pilar de teste
        pillar = next((p for p in data if p["id"] == sample_pillar.id), None)
        assert pillar is not None
        assert "indicator_pillars" in pillar

