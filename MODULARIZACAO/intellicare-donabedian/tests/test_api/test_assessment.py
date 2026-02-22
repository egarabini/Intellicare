"""
Tests for Assessment API endpoints.
"""

import pytest
from httpx import AsyncClient
from datetime import date, timedelta

from donabedian.models.pillar import Pillar
from donabedian.models.indicator import Indicator
from donabedian.models.measurement import Measurement


@pytest.mark.unit
@pytest.mark.api
class TestAssessmentAPI:
    """Test cases for Assessment API endpoints."""
    
    async def test_assess_quality_empty_database(self, client: AsyncClient):
        """Test quality assessment with empty database."""
        response = await client.post("/api/v1/assess", json={})
        
        assert response.status_code == 200
        data = response.json()
        
        assert "overall_score" in data
        assert "pillar_scores" in data
        assert "triad_scores" in data
        assert data["overall_score"] == 0.0
    
    async def test_assess_quality_with_data(
        self,
        client: AsyncClient,
        sample_indicator_pillar,
        sample_measurement: Measurement
    ):
        """Test quality assessment with data."""
        response = await client.post("/api/v1/assess", json={})
        
        assert response.status_code == 200
        data = response.json()
        
        assert "overall_score" in data
        assert "pillar_scores" in data
        assert "triad_scores" in data
        assert isinstance(data["pillar_scores"], list)
        assert isinstance(data["triad_scores"], list)
    
    async def test_assess_quality_with_period_filter(self, client: AsyncClient):
        """Test quality assessment with period filter."""
        request_data = {
            "period_start": str(date.today() - timedelta(days=30)),
            "period_end": str(date.today()),
        }
        
        response = await client.post("/api/v1/assess", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "period_start" in data
        assert "period_end" in data
    
    async def test_assess_quality_with_pillar_filter(
        self,
        client: AsyncClient,
        sample_pillar: Pillar
    ):
        """Test quality assessment with pillar filter."""
        request_data = {
            "pillar_ids": [sample_pillar.id],
        }
        
        response = await client.post("/api/v1/assess", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "pillar_scores" in data
    
    async def test_assess_quality_with_indicator_filter(
        self,
        client: AsyncClient,
        sample_indicator: Indicator
    ):
        """Test quality assessment with indicator filter."""
        request_data = {
            "indicator_ids": [sample_indicator.id],
        }
        
        response = await client.post("/api/v1/assess", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "pillar_scores" in data
    
    async def test_assess_pillar_by_id(
        self,
        client: AsyncClient,
        sample_pillar: Pillar
    ):
        """Test assessing a specific pillar."""
        response = await client.get(f"/api/v1/assess/pillar/{sample_pillar.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "pillar_id" in data
        assert "pillar_name" in data
        assert "score" in data
        assert data["pillar_id"] == sample_pillar.id
    
    async def test_assess_pillar_not_found(self, client: AsyncClient):
        """Test assessing a non-existent pillar."""
        response = await client.get("/api/v1/assess/pillar/99999")
        
        assert response.status_code == 404
    
    async def test_assess_pillar_with_period(
        self,
        client: AsyncClient,
        sample_pillar: Pillar
    ):
        """Test assessing a pillar with period filter."""
        params = {
            "period_start": str(date.today() - timedelta(days=30)),
            "period_end": str(date.today()),
        }
        
        response = await client.get(f"/api/v1/assess/pillar/{sample_pillar.id}", params=params)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "score" in data
    
    async def test_assess_triad_structure(self, client: AsyncClient):
        """Test assessing structure dimension."""
        response = await client.get("/api/v1/assess/triad/structure")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "dimension" in data
        assert "score" in data
        assert data["dimension"] == "structure"
    
    async def test_assess_triad_process(self, client: AsyncClient):
        """Test assessing process dimension."""
        response = await client.get("/api/v1/assess/triad/process")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["dimension"] == "process"
    
    async def test_assess_triad_outcome(self, client: AsyncClient):
        """Test assessing outcome dimension."""
        response = await client.get("/api/v1/assess/triad/outcome")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["dimension"] == "outcome"
    
    async def test_assess_triad_invalid_dimension(self, client: AsyncClient):
        """Test assessing with invalid dimension."""
        response = await client.get("/api/v1/assess/triad/invalid")
        
        assert response.status_code in [400, 422]
    
    async def test_assess_triad_with_period(self, client: AsyncClient):
        """Test assessing triad with period filter."""
        params = {
            "period_start": str(date.today() - timedelta(days=30)),
            "period_end": str(date.today()),
        }
        
        response = await client.get("/api/v1/assess/triad/structure", params=params)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "score" in data
    
    async def test_assessment_response_structure(self, client: AsyncClient):
        """Test that assessment response has correct structure."""
        response = await client.post("/api/v1/assess", json={})
        
        assert response.status_code == 200
        data = response.json()
        
        required_fields = [
            "overall_score",
            "pillar_scores",
            "triad_scores",
            "period_start",
            "period_end",
        ]
        for field in required_fields:
            assert field in data

