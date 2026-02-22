"""
Testes de integração para endpoints de Avaliação de Qualidade.
"""
import pytest
from httpx import AsyncClient
from datetime import datetime


@pytest.mark.asyncio
class TestAssessmentIntegration:
    """Testes de integração para endpoints de Avaliação."""
    
    async def test_get_quality_assessment(
        self, 
        client: AsyncClient, 
        sample_pillar, 
        sample_indicator, 
        sample_indicator_pillar,
        sample_measurement
    ):
        """Testa avaliação de qualidade geral."""
        response = await client.get(
            "/api/v1/assessment/quality"
            f"?period_start=2024-01-01T00:00:00"
            f"&period_end=2024-01-31T23:59:59"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "overall_score" in data
        assert "total_indicators" in data
        assert "indicators_achieved" in data
        assert "achievement_rate" in data
        assert "pillars" in data
        assert isinstance(data["pillars"], list)
    
    async def test_get_pillar_assessment(
        self,
        client: AsyncClient,
        sample_pillar,
        sample_indicator,
        sample_indicator_pillar,
        sample_measurement
    ):
        """Testa avaliação de qualidade por pilar."""
        response = await client.get(
            f"/api/v1/assessment/pillar/{sample_pillar.id}"
            f"?period_start=2024-01-01T00:00:00"
            f"&period_end=2024-01-31T23:59:59"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["pillar_id"] == sample_pillar.id
        assert data["pillar_name"] == sample_pillar.name
        assert "score" in data
        assert "total_indicators" in data
        assert "indicators" in data
        assert isinstance(data["indicators"], list)
    
    async def test_get_indicator_assessment(
        self,
        client: AsyncClient,
        sample_indicator,
        sample_measurement
    ):
        """Testa avaliação de indicador específico."""
        response = await client.get(
            f"/api/v1/assessment/indicator/{sample_indicator.id}"
            f"?period_start=2024-01-01T00:00:00"
            f"&period_end=2024-01-31T23:59:59"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["indicator_id"] == sample_indicator.id
        assert data["indicator_name"] == sample_indicator.name
        assert "current_value" in data
        assert "target_value" in data
        assert "status" in data
        assert "measurements_count" in data
    
    async def test_assessment_without_data(self, client: AsyncClient):
        """Testa avaliação sem dados no período."""
        response = await client.get(
            "/api/v1/assessment/quality"
            f"?period_start=2025-01-01T00:00:00"
            f"&period_end=2025-01-31T23:59:59"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_indicators"] == 0
        assert data["overall_score"] == 0.0
    
    async def test_assessment_invalid_period(self, client: AsyncClient):
        """Testa avaliação com período inválido."""
        response = await client.get(
            "/api/v1/assessment/quality"
            f"?period_start=2024-12-31T00:00:00"
            f"&period_end=2024-01-01T23:59:59"  # Fim antes do início
        )
        
        assert response.status_code == 422

