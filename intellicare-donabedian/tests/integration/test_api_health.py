"""
Testes de integração para endpoint de Health Check.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestHealthIntegration:
    """Testes de integração para Health Check."""
    
    async def test_health_check(self, client: AsyncClient):
        """Testa health check da API."""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert data["status"] == "healthy"
        assert "database" in data
        assert "timestamp" in data
    
    async def test_health_check_database_connection(self, client: AsyncClient):
        """Testa se health check verifica conexão com banco."""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Deve indicar que o banco está conectado
        assert data["database"] in ["connected", "healthy"]

