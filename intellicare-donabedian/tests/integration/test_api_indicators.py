"""
Testes de integração para endpoints de Indicadores.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestIndicatorsIntegration:
    """Testes de integração para endpoints de Indicadores."""
    
    async def test_create_indicator(self, client: AsyncClient):
        """Testa criação de indicador via API."""
        response = await client.post(
            "/api/v1/indicators",
            json={
                "name": "Taxa de Ocupação",
                "description": "Percentual de leitos ocupados",
                "formula": "(leitos_ocupados / total_leitos) * 100",
                "unit": "%",
                "target_value": 85.0,
                "target_operator": "<=",
                "triad_dimension": "structure"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Taxa de Ocupação"
        assert data["unit"] == "%"
        assert data["target_value"] == 85.0
        assert "id" in data
    
    async def test_list_indicators(self, client: AsyncClient, sample_indicator):
        """Testa listagem de indicadores via API."""
        response = await client.get("/api/v1/indicators")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["name"] == sample_indicator.name
    
    async def test_get_indicator(self, client: AsyncClient, sample_indicator):
        """Testa busca de indicador específico via API."""
        response = await client.get(f"/api/v1/indicators/{sample_indicator.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_indicator.id
        assert data["name"] == sample_indicator.name
        assert data["formula"] == sample_indicator.formula
    
    async def test_update_indicator(self, client: AsyncClient, sample_indicator):
        """Testa atualização de indicador via API."""
        response = await client.put(
            f"/api/v1/indicators/{sample_indicator.id}",
            json={
                "name": "Taxa de Ocupação Atualizada",
                "description": "Nova descrição",
                "formula": "nova_formula",
                "unit": "%",
                "target_value": 90.0,
                "target_operator": ">=",
                "triad_dimension": "process"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Taxa de Ocupação Atualizada"
        assert data["target_value"] == 90.0
        assert data["triad_dimension"] == "process"
    
    async def test_delete_indicator(self, client: AsyncClient, sample_indicator):
        """Testa exclusão de indicador via API."""
        response = await client.delete(f"/api/v1/indicators/{sample_indicator.id}")
        
        assert response.status_code == 204
        
        # Verifica que foi deletado
        response = await client.get(f"/api/v1/indicators/{sample_indicator.id}")
        assert response.status_code == 404
    
    async def test_get_indicator_not_found(self, client: AsyncClient):
        """Testa busca de indicador inexistente."""
        response = await client.get("/api/v1/indicators/99999")
        
        assert response.status_code == 404
    
    async def test_create_indicator_validation_error(self, client: AsyncClient):
        """Testa validação ao criar indicador com dados inválidos."""
        response = await client.post(
            "/api/v1/indicators",
            json={
                "name": "Teste",
                "description": "Descrição",
                # Faltando campos obrigatórios: formula, unit
                "target_value": 85.0
            }
        )
        
        assert response.status_code == 422
    
    async def test_filter_indicators_by_triad(self, client: AsyncClient, sample_indicator):
        """Testa filtro de indicadores por dimensão da tríade."""
        response = await client.get("/api/v1/indicators?triad_dimension=structure")
        
        assert response.status_code == 200
        data = response.json()
        
        # Todos devem ser da dimensão structure
        for indicator in data:
            assert indicator["triad_dimension"] == "structure"
    
    async def test_list_indicators_with_measurements(self, client: AsyncClient, sample_indicator, sample_measurement):
        """Testa listagem de indicadores com medições associadas."""
        response = await client.get("/api/v1/indicators")
        
        assert response.status_code == 200
        data = response.json()
        
        # Encontra o indicador de teste
        indicator = next((i for i in data if i["id"] == sample_indicator.id), None)
        assert indicator is not None
        assert "measurements" in indicator

