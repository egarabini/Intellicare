"""
Tests for Indicators API endpoints.
"""

import pytest
from httpx import AsyncClient

from donabedian.models.indicator import Indicator


@pytest.mark.unit
@pytest.mark.api
class TestIndicatorsAPI:
    """Test cases for Indicators CRUD API."""
    
    async def test_list_indicators_empty(self, client: AsyncClient):
        """Test listing indicators when database is empty."""
        response = await client.get("/api/v1/indicators")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert len(data["items"]) == 0
    
    async def test_list_indicators_with_data(self, client: AsyncClient, sample_indicator: Indicator):
        """Test listing indicators with data."""
        response = await client.get("/api/v1/indicators")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["items"]) == 1
        assert data["total"] == 1
        assert data["items"][0]["name"] == sample_indicator.name
    
    async def test_list_indicators_pagination(self, client: AsyncClient):
        """Test indicators pagination."""
        response = await client.get("/api/v1/indicators?page=1&page_size=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["page"] == 1
        assert data["page_size"] == 10
    
    async def test_get_indicator_by_id(self, client: AsyncClient, sample_indicator: Indicator):
        """Test getting an indicator by ID."""
        response = await client.get(f"/api/v1/indicators/{sample_indicator.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == sample_indicator.id
        assert data["name"] == sample_indicator.name
        assert data["triad_dimension"] == sample_indicator.triad_dimension.value
    
    async def test_get_indicator_not_found(self, client: AsyncClient):
        """Test getting a non-existent indicator."""
        response = await client.get("/api/v1/indicators/99999")
        
        assert response.status_code == 404
    
    async def test_create_indicator(self, client: AsyncClient):
        """Test creating a new indicator."""
        indicator_data = {
            "name": "Taxa de Mortalidade",
            "description": "Percentual de óbitos",
            "triad_dimension": "outcome",
            "target_value": 2.0,
            "target_operator": "<=",
            "unit": "%",
        }
        
        response = await client.post("/api/v1/indicators", json=indicator_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == indicator_data["name"]
        assert data["triad_dimension"] == indicator_data["triad_dimension"]
        assert data["target_value"] == indicator_data["target_value"]
        assert "id" in data
    
    async def test_create_indicator_missing_required_fields(self, client: AsyncClient):
        """Test creating an indicator with missing required fields."""
        indicator_data = {
            "name": "Test",
            # Missing triad_dimension, target_value, target_operator
        }
        
        response = await client.post("/api/v1/indicators", json=indicator_data)
        
        assert response.status_code == 422
    
    async def test_create_indicator_invalid_triad_dimension(self, client: AsyncClient):
        """Test creating an indicator with invalid triad dimension."""
        indicator_data = {
            "name": "Test",
            "triad_dimension": "invalid",
            "target_value": 85.0,
            "target_operator": ">=",
        }
        
        response = await client.post("/api/v1/indicators", json=indicator_data)
        
        assert response.status_code == 422
    
    async def test_create_indicator_invalid_operator(self, client: AsyncClient):
        """Test creating an indicator with invalid operator."""
        indicator_data = {
            "name": "Test",
            "triad_dimension": "structure",
            "target_value": 85.0,
            "target_operator": ">",  # Invalid
        }
        
        response = await client.post("/api/v1/indicators", json=indicator_data)
        
        assert response.status_code == 422
    
    async def test_update_indicator(self, client: AsyncClient, sample_indicator: Indicator):
        """Test updating an indicator."""
        update_data = {
            "target_value": 90.0,
        }
        
        response = await client.put(f"/api/v1/indicators/{sample_indicator.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["target_value"] == update_data["target_value"]
        assert data["name"] == sample_indicator.name  # Unchanged
    
    async def test_update_indicator_not_found(self, client: AsyncClient):
        """Test updating a non-existent indicator."""
        update_data = {
            "target_value": 90.0,
        }
        
        response = await client.put("/api/v1/indicators/99999", json=update_data)
        
        assert response.status_code == 404
    
    async def test_delete_indicator(self, client: AsyncClient, sample_indicator: Indicator):
        """Test deleting an indicator."""
        response = await client.delete(f"/api/v1/indicators/{sample_indicator.id}")
        
        assert response.status_code == 204
        
        # Verify deletion
        get_response = await client.get(f"/api/v1/indicators/{sample_indicator.id}")
        assert get_response.status_code == 404
    
    async def test_delete_indicator_not_found(self, client: AsyncClient):
        """Test deleting a non-existent indicator."""
        response = await client.delete("/api/v1/indicators/99999")
        
        assert response.status_code == 404
    
    async def test_indicator_response_structure(self, client: AsyncClient, sample_indicator: Indicator):
        """Test that indicator response has correct structure."""
        response = await client.get(f"/api/v1/indicators/{sample_indicator.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        required_fields = [
            "id", "name", "triad_dimension", "target_value",
            "target_operator", "created_at", "updated_at"
        ]
        for field in required_fields:
            assert field in data

