"""
Testes de integração para endpoints de Medições.
"""
import pytest
from httpx import AsyncClient
from datetime import datetime


@pytest.mark.asyncio
class TestMeasurementsIntegration:
    """Testes de integração para endpoints de Medições."""
    
    async def test_create_measurement(self, client: AsyncClient, sample_indicator):
        """Testa criação de medição via API."""
        response = await client.post(
            "/api/v1/measurements",
            json={
                "indicator_id": sample_indicator.id,
                "value": 82.5,
                "period_start": "2024-01-01T00:00:00",
                "period_end": "2024-01-31T23:59:59",
                "period_type": "monthly"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["indicator_id"] == sample_indicator.id
        assert data["value"] == 82.5
        assert data["period_type"] == "monthly"
        assert "status" in data  # Status calculado automaticamente
        assert "id" in data
    
    async def test_list_measurements(self, client: AsyncClient, sample_measurement):
        """Testa listagem de medições via API."""
        response = await client.get("/api/v1/measurements")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["value"] == sample_measurement.value
    
    async def test_get_measurement(self, client: AsyncClient, sample_measurement):
        """Testa busca de medição específica via API."""
        response = await client.get(f"/api/v1/measurements/{sample_measurement.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_measurement.id
        assert data["value"] == sample_measurement.value
    
    async def test_update_measurement(self, client: AsyncClient, sample_measurement):
        """Testa atualização de medição via API."""
        response = await client.put(
            f"/api/v1/measurements/{sample_measurement.id}",
            json={
                "indicator_id": sample_measurement.indicator_id,
                "value": 88.0,
                "period_start": "2024-02-01T00:00:00",
                "period_end": "2024-02-29T23:59:59",
                "period_type": "monthly"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["value"] == 88.0
    
    async def test_delete_measurement(self, client: AsyncClient, sample_measurement):
        """Testa exclusão de medição via API."""
        response = await client.delete(f"/api/v1/measurements/{sample_measurement.id}")
        
        assert response.status_code == 204
        
        # Verifica que foi deletado
        response = await client.get(f"/api/v1/measurements/{sample_measurement.id}")
        assert response.status_code == 404
    
    async def test_get_measurement_not_found(self, client: AsyncClient):
        """Testa busca de medição inexistente."""
        response = await client.get("/api/v1/measurements/99999")
        
        assert response.status_code == 404
    
    async def test_create_measurement_validation_error(self, client: AsyncClient):
        """Testa validação ao criar medição com dados inválidos."""
        response = await client.post(
            "/api/v1/measurements",
            json={
                "indicator_id": 99999,  # Indicador inexistente
                "value": 82.5,
                "period_start": "2024-01-01T00:00:00",
                "period_end": "2024-01-31T23:59:59"
                # Faltando period_type
            }
        )
        
        assert response.status_code == 422
    
    async def test_filter_measurements_by_indicator(self, client: AsyncClient, sample_measurement):
        """Testa filtro de medições por indicador."""
        response = await client.get(f"/api/v1/measurements?indicator_id={sample_measurement.indicator_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Todas devem ser do mesmo indicador
        for measurement in data:
            assert measurement["indicator_id"] == sample_measurement.indicator_id
    
    async def test_filter_measurements_by_period(self, client: AsyncClient, sample_measurement):
        """Testa filtro de medições por período."""
        response = await client.get(
            "/api/v1/measurements"
            f"?period_start=2024-01-01T00:00:00"
            f"&period_end=2024-12-31T23:59:59"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
    
    async def test_measurement_status_calculation(self, client: AsyncClient, sample_indicator):
        """Testa cálculo automático de status da medição."""
        # Criar medição com valor dentro da meta
        response = await client.post(
            "/api/v1/measurements",
            json={
                "indicator_id": sample_indicator.id,
                "value": 80.0,  # Abaixo da meta de 85 (target_operator: <=)
                "period_start": "2024-01-01T00:00:00",
                "period_end": "2024-01-31T23:59:59",
                "period_type": "monthly"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "achieved"  # Deve estar dentro da meta

