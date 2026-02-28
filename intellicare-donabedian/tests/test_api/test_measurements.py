"""
Tests for Measurements API endpoints.
"""

import pytest
from httpx import AsyncClient
from datetime import date, timedelta

from donabedian.models.measurement import Measurement
from donabedian.models.indicator import Indicator


@pytest.mark.unit
@pytest.mark.api
class TestMeasurementsAPI:
    """Test cases for Measurements CRUD API."""
    
    async def test_list_measurements_empty(self, client: AsyncClient):
        """Test listing measurements when database is empty."""
        response = await client.get("/api/v1/measurements")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert len(data["items"]) == 0
    
    async def test_list_measurements_with_data(self, client: AsyncClient, sample_measurement: Measurement):
        """Test listing measurements with data."""
        response = await client.get("/api/v1/measurements")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["items"]) == 1
        assert data["items"][0]["value"] == sample_measurement.value
    
    async def test_get_measurement_by_id(self, client: AsyncClient, sample_measurement: Measurement):
        """Test getting a measurement by ID."""
        response = await client.get(f"/api/v1/measurements/{sample_measurement.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == sample_measurement.id
        assert data["value"] == sample_measurement.value
        assert data["status"] == sample_measurement.status.value
    
    async def test_get_measurement_not_found(self, client: AsyncClient):
        """Test getting a non-existent measurement."""
        response = await client.get("/api/v1/measurements/99999")
        
        assert response.status_code == 404
    
    async def test_create_measurement(self, client: AsyncClient, sample_indicator: Indicator):
        """Test creating a new measurement."""
        measurement_data = {
            "indicator_id": sample_indicator.id,
            "period_start": str(date.today() - timedelta(days=7)),
            "period_end": str(date.today()),
            "value": 88.0,
            "status": "green",
        }
        
        response = await client.post("/api/v1/measurements", json=measurement_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["indicator_id"] == measurement_data["indicator_id"]
        assert data["value"] == measurement_data["value"]
        assert data["status"] == measurement_data["status"]
        assert "id" in data
    
    async def test_create_measurement_missing_required_fields(self, client: AsyncClient):
        """Test creating a measurement with missing required fields."""
        measurement_data = {
            "value": 88.0,
            # Missing indicator_id, period_start, period_end, status
        }
        
        response = await client.post("/api/v1/measurements", json=measurement_data)
        
        assert response.status_code == 422
    
    async def test_create_measurement_invalid_indicator(self, client: AsyncClient):
        """Test creating a measurement with invalid indicator_id."""
        measurement_data = {
            "indicator_id": 99999,
            "period_start": str(date.today() - timedelta(days=7)),
            "period_end": str(date.today()),
            "value": 88.0,
            "status": "green",
        }
        
        response = await client.post("/api/v1/measurements", json=measurement_data)
        
        assert response.status_code in [400, 404]
    
    async def test_create_measurement_with_notes(self, client: AsyncClient, sample_indicator: Indicator):
        """Test creating a measurement with notes."""
        measurement_data = {
            "indicator_id": sample_indicator.id,
            "period_start": str(date.today() - timedelta(days=7)),
            "period_end": str(date.today()),
            "value": 88.0,
            "status": "green",
            "notes": "Test notes",
        }
        
        response = await client.post("/api/v1/measurements", json=measurement_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["notes"] == "Test notes"
    
    async def test_update_measurement(self, client: AsyncClient, sample_measurement: Measurement):
        """Test updating a measurement."""
        update_data = {
            "value": 92.0,
            "status": "green",
        }
        
        response = await client.put(f"/api/v1/measurements/{sample_measurement.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["value"] == update_data["value"]
        assert data["status"] == update_data["status"]
    
    async def test_update_measurement_not_found(self, client: AsyncClient):
        """Test updating a non-existent measurement."""
        update_data = {
            "value": 92.0,
        }
        
        response = await client.put("/api/v1/measurements/99999", json=update_data)
        
        assert response.status_code == 404
    
    async def test_delete_measurement(self, client: AsyncClient, sample_measurement: Measurement):
        """Test deleting a measurement."""
        response = await client.delete(f"/api/v1/measurements/{sample_measurement.id}")
        
        assert response.status_code == 204
        
        # Verify deletion
        get_response = await client.get(f"/api/v1/measurements/{sample_measurement.id}")
        assert get_response.status_code == 404
    
    async def test_delete_measurement_not_found(self, client: AsyncClient):
        """Test deleting a non-existent measurement."""
        response = await client.delete("/api/v1/measurements/99999")
        
        assert response.status_code == 404
    
    async def test_measurement_response_structure(self, client: AsyncClient, sample_measurement: Measurement):
        """Test that measurement response has correct structure."""
        response = await client.get(f"/api/v1/measurements/{sample_measurement.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        required_fields = [
            "id", "indicator_id", "period_start", "period_end",
            "value", "status", "created_at", "updated_at"
        ]
        for field in required_fields:
            assert field in data
    
    async def test_list_measurements_by_indicator(
        self,
        client: AsyncClient,
        sample_indicator: Indicator,
        sample_measurement: Measurement
    ):
        """Test filtering measurements by indicator."""
        response = await client.get(f"/api/v1/measurements?indicator_id={sample_indicator.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["items"]) >= 1
        for item in data["items"]:
            assert item["indicator_id"] == sample_indicator.id

