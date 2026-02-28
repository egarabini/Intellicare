"""
Tests for Pillars API endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from donabedian.models.pillar import Pillar


@pytest.mark.unit
@pytest.mark.api
class TestPillarsAPI:
    """Test cases for Pillars CRUD API."""
    
    async def test_list_pillars_empty(self, client: AsyncClient):
        """Test listing pillars when database is empty."""
        response = await client.get("/api/v1/pillars")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 0
    
    async def test_list_pillars_with_data(self, client: AsyncClient, sample_pillar: Pillar):
        """Test listing pillars with data."""
        response = await client.get("/api/v1/pillars")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["name"] == sample_pillar.name
        assert data[0]["code"] == sample_pillar.code
    
    async def test_get_pillar_by_id(self, client: AsyncClient, sample_pillar: Pillar):
        """Test getting a pillar by ID."""
        response = await client.get(f"/api/v1/pillars/{sample_pillar.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == sample_pillar.id
        assert data["name"] == sample_pillar.name
        assert data["code"] == sample_pillar.code
    
    async def test_get_pillar_not_found(self, client: AsyncClient):
        """Test getting a non-existent pillar."""
        response = await client.get("/api/v1/pillars/99999")
        
        assert response.status_code == 404
    
    async def test_create_pillar(self, client: AsyncClient):
        """Test creating a new pillar."""
        pillar_data = {
            "name": "Efetividade",
            "description": "Grau em que os cuidados atingem os resultados desejados",
            "code": "EFT",
        }
        
        response = await client.post("/api/v1/pillars", json=pillar_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == pillar_data["name"]
        assert data["code"] == pillar_data["code"]
        assert "id" in data
        assert "created_at" in data
    
    async def test_create_pillar_missing_required_fields(self, client: AsyncClient):
        """Test creating a pillar with missing required fields."""
        pillar_data = {
            "name": "Efetividade",
            # Missing code
        }
        
        response = await client.post("/api/v1/pillars", json=pillar_data)
        
        assert response.status_code == 422  # Validation error
    
    async def test_create_pillar_duplicate_name(self, client: AsyncClient, sample_pillar: Pillar):
        """Test creating a pillar with duplicate name."""
        pillar_data = {
            "name": sample_pillar.name,
            "description": "Test",
            "code": "NEW",
        }
        
        response = await client.post("/api/v1/pillars", json=pillar_data)
        
        assert response.status_code in [400, 409]  # Bad request or conflict
    
    async def test_update_pillar(self, client: AsyncClient, sample_pillar: Pillar):
        """Test updating a pillar."""
        update_data = {
            "description": "Updated description",
        }
        
        response = await client.put(f"/api/v1/pillars/{sample_pillar.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == sample_pillar.id
        assert data["description"] == update_data["description"]
        assert data["name"] == sample_pillar.name  # Unchanged
    
    async def test_update_pillar_not_found(self, client: AsyncClient):
        """Test updating a non-existent pillar."""
        update_data = {
            "description": "Updated description",
        }
        
        response = await client.put("/api/v1/pillars/99999", json=update_data)
        
        assert response.status_code == 404
    
    async def test_update_pillar_all_fields(self, client: AsyncClient, sample_pillar: Pillar):
        """Test updating all pillar fields."""
        update_data = {
            "name": "Updated Name",
            "description": "Updated description",
            "code": "UPD",
        }
        
        response = await client.put(f"/api/v1/pillars/{sample_pillar.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
        assert data["code"] == update_data["code"]
    
    async def test_delete_pillar(self, client: AsyncClient, sample_pillar: Pillar):
        """Test deleting a pillar."""
        response = await client.delete(f"/api/v1/pillars/{sample_pillar.id}")
        
        assert response.status_code == 204
        
        # Verify deletion
        get_response = await client.get(f"/api/v1/pillars/{sample_pillar.id}")
        assert get_response.status_code == 404
    
    async def test_delete_pillar_not_found(self, client: AsyncClient):
        """Test deleting a non-existent pillar."""
        response = await client.delete("/api/v1/pillars/99999")
        
        assert response.status_code == 404
    
    async def test_pillar_response_structure(self, client: AsyncClient, sample_pillar: Pillar):
        """Test that pillar response has correct structure."""
        response = await client.get(f"/api/v1/pillars/{sample_pillar.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["id", "name", "code", "created_at", "updated_at"]
        for field in required_fields:
            assert field in data

