"""
Tests for Dashboard API Client.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx

from donabedian.dashboard.api_client import DonabedianAPIClient


@pytest.mark.unit
@pytest.mark.dashboard
class TestDonabedianAPIClient:
    """Test cases for DonabedianAPIClient."""
    
    def test_client_initialization_default(self):
        """Test client initialization with default base URL."""
        client = DonabedianAPIClient()
        
        assert client.base_url == "http://localhost:8000"
        assert client.timeout == 30.0
        assert client.max_retries == 3
    
    def test_client_initialization_custom_url(self):
        """Test client initialization with custom base URL."""
        custom_url = "http://api.example.com:8080"
        client = DonabedianAPIClient(base_url=custom_url)
        
        assert client.base_url == custom_url
    
    def test_client_initialization_custom_timeout(self):
        """Test client initialization with custom timeout."""
        client = DonabedianAPIClient(timeout=60.0)
        
        assert client.timeout == 60.0
    
    @pytest.mark.asyncio
    async def test_get_method_success(self):
        """Test GET method with successful response."""
        client = DonabedianAPIClient()
        
        with patch.object(httpx.AsyncClient, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_get.return_value = mock_response
            
            result = await client.get("/test")
            
            assert result == {"status": "ok"}
            mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_method_with_params(self):
        """Test GET method with query parameters."""
        client = DonabedianAPIClient()
        
        with patch.object(httpx.AsyncClient, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"data": []}
            mock_get.return_value = mock_response
            
            params = {"page": 1, "page_size": 10}
            result = await client.get("/test", params=params)
            
            assert result == {"data": []}
    
    @pytest.mark.asyncio
    async def test_post_method_success(self):
        """Test POST method with successful response."""
        client = DonabedianAPIClient()
        
        with patch.object(httpx.AsyncClient, 'post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"id": 1, "name": "Test"}
            mock_post.return_value = mock_response
            
            data = {"name": "Test"}
            result = await client.post("/test", json=data)
            
            assert result == {"id": 1, "name": "Test"}
    
    @pytest.mark.asyncio
    async def test_put_method_success(self):
        """Test PUT method with successful response."""
        client = DonabedianAPIClient()
        
        with patch.object(httpx.AsyncClient, 'put') as mock_put:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"id": 1, "name": "Updated"}
            mock_put.return_value = mock_response
            
            data = {"name": "Updated"}
            result = await client.put("/test/1", json=data)
            
            assert result == {"id": 1, "name": "Updated"}
    
    @pytest.mark.asyncio
    async def test_delete_method_success(self):
        """Test DELETE method with successful response."""
        client = DonabedianAPIClient()
        
        with patch.object(httpx.AsyncClient, 'delete') as mock_delete:
            mock_response = Mock()
            mock_response.status_code = 204
            mock_delete.return_value = mock_response
            
            result = await client.delete("/test/1")
            
            assert result is None  # 204 No Content
    
    @pytest.mark.asyncio
    async def test_http_error_handling(self):
        """Test HTTP error handling."""
        client = DonabedianAPIClient()
        
        with patch.object(httpx.AsyncClient, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Not Found", request=Mock(), response=mock_response
            )
            mock_get.return_value = mock_response
            
            with pytest.raises(httpx.HTTPStatusError):
                await client.get("/test/99999")
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test timeout handling."""
        client = DonabedianAPIClient(timeout=0.001)
        
        with patch.object(httpx.AsyncClient, 'get') as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Timeout")
            
            with pytest.raises(httpx.TimeoutException):
                await client.get("/test")
    
    @pytest.mark.asyncio
    async def test_get_pillars(self):
        """Test get_pillars method."""
        client = DonabedianAPIClient()
        
        with patch.object(client, 'get') as mock_get:
            mock_get.return_value = [{"id": 1, "name": "Eficácia"}]
            
            result = await client.get_pillars()
            
            assert len(result) == 1
            assert result[0]["name"] == "Eficácia"
            mock_get.assert_called_once_with("/api/v1/pillars")
    
    @pytest.mark.asyncio
    async def test_get_indicators(self):
        """Test get_indicators method."""
        client = DonabedianAPIClient()
        
        with patch.object(client, 'get') as mock_get:
            mock_get.return_value = {
                "items": [{"id": 1, "name": "Taxa de Ocupação"}],
                "total": 1
            }
            
            result = await client.get_indicators()
            
            assert result["total"] == 1
            mock_get.assert_called_once_with("/api/v1/indicators", params=None)
    
    @pytest.mark.asyncio
    async def test_get_dashboard(self):
        """Test get_dashboard method."""
        client = DonabedianAPIClient()
        
        with patch.object(client, 'get') as mock_get:
            mock_get.return_value = {
                "overall_score": 85.5,
                "total_pillars": 7
            }
            
            result = await client.get_dashboard()
            
            assert result["overall_score"] == 85.5
            mock_get.assert_called_once_with("/api/v1/dashboard", params=None)

