"""
Tests for IndicatorPillars API endpoints.
"""

import pytest
from httpx import AsyncClient

from donabedian.models.indicator_pillar import IndicatorPillar
from donabedian.models.indicator import Indicator
from donabedian.models.pillar import Pillar


@pytest.mark.unit
@pytest.mark.api
class TestIndicatorPillarsAPI:
    """Test cases for IndicatorPillars CRUD API."""
    
    async def test_list_indicator_pillars_empty(self, client: AsyncClient):
        """Test listing indicator-pillar associations when database is empty."""
        response = await client.get("/api/v1/indicator-pillars")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 0
    
    async def test_list_indicator_pillars_with_data(
        self,
        client: AsyncClient,
        sample_indicator_pillar: IndicatorPillar
    ):
        """Test listing indicator-pillar associations with data."""
        response = await client.get("/api/v1/indicator-pillars")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        assert data[0]["indicator_id"] == sample_indicator_pillar.indicator_id
        assert data[0]["pillar_id"] == sample_indicator_pillar.pillar_id
    
    async def test_get_indicator_pillar_by_id(
        self,
        client: AsyncClient,
        sample_indicator_pillar: IndicatorPillar
    ):
        """Test getting an indicator-pillar association by ID."""
        response = await client.get(f"/api/v1/indicator-pillars/{sample_indicator_pillar.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == sample_indicator_pillar.id
        assert data["weight"] == sample_indicator_pillar.weight
    
    async def test_get_indicator_pillar_not_found(self, client: AsyncClient):
        """Test getting a non-existent indicator-pillar association."""
        response = await client.get("/api/v1/indicator-pillars/99999")
        
        assert response.status_code == 404
    
    async def test_create_indicator_pillar(
        self,
        client: AsyncClient,
        sample_indicator: Indicator,
        sample_pillar: Pillar
    ):
        """Test creating a new indicator-pillar association."""
        # First, delete any existing association
        await client.delete(f"/api/v1/indicator-pillars/1")
        
        assoc_data = {
            "indicator_id": sample_indicator.id,
            "pillar_id": sample_pillar.id,
            "weight": 2.0,
        }
        
        response = await client.post("/api/v1/indicator-pillars", json=assoc_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["indicator_id"] == assoc_data["indicator_id"]
        assert data["pillar_id"] == assoc_data["pillar_id"]
        assert data["weight"] == assoc_data["weight"]
        assert "id" in data
    
    async def test_create_indicator_pillar_default_weight(
        self,
        client: AsyncClient,
        db_session
    ):
        """Test creating an indicator-pillar association with default weight."""
        # Create new indicator and pillar for this test
        from donabedian.models.indicator import Indicator, TriadDimension
        from donabedian.models.pillar import Pillar
        
        indicator = Indicator(
            name="Test Indicator 2",
            triad_dimension=TriadDimension.STRUCTURE,
            target_value=85.0,
            target_operator=">=",
        )
        pillar = Pillar(name="Test Pillar 2", code="TP2")
        
        db_session.add(indicator)
        db_session.add(pillar)
        await db_session.commit()
        await db_session.refresh(indicator)
        await db_session.refresh(pillar)
        
        assoc_data = {
            "indicator_id": indicator.id,
            "pillar_id": pillar.id,
        }
        
        response = await client.post("/api/v1/indicator-pillars", json=assoc_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["weight"] == 1.0  # Default weight
    
    async def test_create_indicator_pillar_missing_required_fields(self, client: AsyncClient):
        """Test creating an indicator-pillar association with missing required fields."""
        assoc_data = {
            "indicator_id": 1,
            # Missing pillar_id
        }
        
        response = await client.post("/api/v1/indicator-pillars", json=assoc_data)
        
        assert response.status_code == 422
    
    async def test_create_indicator_pillar_invalid_indicator(self, client: AsyncClient):
        """Test creating an association with invalid indicator_id."""
        assoc_data = {
            "indicator_id": 99999,
            "pillar_id": 1,
            "weight": 1.0,
        }
        
        response = await client.post("/api/v1/indicator-pillars", json=assoc_data)
        
        assert response.status_code in [400, 404]
    
    async def test_update_indicator_pillar(
        self,
        client: AsyncClient,
        sample_indicator_pillar: IndicatorPillar
    ):
        """Test updating an indicator-pillar association."""
        update_data = {
            "weight": 3.0,
        }
        
        response = await client.put(
            f"/api/v1/indicator-pillars/{sample_indicator_pillar.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["weight"] == update_data["weight"]
    
    async def test_update_indicator_pillar_not_found(self, client: AsyncClient):
        """Test updating a non-existent indicator-pillar association."""
        update_data = {
            "weight": 3.0,
        }
        
        response = await client.put("/api/v1/indicator-pillars/99999", json=update_data)
        
        assert response.status_code == 404
    
    async def test_delete_indicator_pillar(
        self,
        client: AsyncClient,
        sample_indicator_pillar: IndicatorPillar
    ):
        """Test deleting an indicator-pillar association."""
        response = await client.delete(f"/api/v1/indicator-pillars/{sample_indicator_pillar.id}")
        
        assert response.status_code == 204
        
        # Verify deletion
        get_response = await client.get(f"/api/v1/indicator-pillars/{sample_indicator_pillar.id}")
        assert get_response.status_code == 404
    
    async def test_delete_indicator_pillar_not_found(self, client: AsyncClient):
        """Test deleting a non-existent indicator-pillar association."""
        response = await client.delete("/api/v1/indicator-pillars/99999")
        
        assert response.status_code == 404

