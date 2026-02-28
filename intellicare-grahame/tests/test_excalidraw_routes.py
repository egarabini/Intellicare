"""Tests for Excalidraw API Routes."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def diagram_data():
    """Sample Excalidraw diagram data."""
    return {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": [
            {
                "id": "element1",
                "type": "rectangle",
                "x": 100,
                "y": 100,
                "width": 200,
                "height": 100,
            }
        ],
        "appState": {"viewBackgroundColor": "#ffffff"},
    }


def test_create_diagram(client: TestClient, diagram_data):
    """Test creating a diagram via API."""
    response = client.post(
        "/api/v1/excalidraw/diagrams",
        json={
            "diagram_data": diagram_data,
            "patient_id": "patient-123",
            "title": "Test Diagram",
            "description": "A test diagram",
            "category": "clinical-diagram",
            "author_id": "practitioner-456",
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "media_id" in data
    assert "document_reference_id" in data
    assert "diagram_url" in data


def test_get_diagram(client: TestClient, diagram_data):
    """Test retrieving a diagram via API."""
    # Create diagram
    create_response = client.post(
        "/api/v1/excalidraw/diagrams",
        json={
            "diagram_data": diagram_data,
            "patient_id": "patient-123",
            "title": "Test Diagram",
        },
    )
    
    media_id = create_response.json()["media_id"]
    
    # Get diagram
    response = client.get(f"/api/v1/excalidraw/diagrams/{media_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == media_id
    assert data["title"] == "Test Diagram"
    assert data["patient_id"] == "patient-123"
    assert data["data"]["type"] == "excalidraw"


def test_get_nonexistent_diagram(client: TestClient):
    """Test retrieving a non-existent diagram."""
    response = client.get("/api/v1/excalidraw/diagrams/nonexistent-id")
    
    assert response.status_code == 404


def test_list_patient_diagrams(client: TestClient, diagram_data):
    """Test listing diagrams for a patient."""
    # Create multiple diagrams
    client.post(
        "/api/v1/excalidraw/diagrams",
        json={
            "diagram_data": diagram_data,
            "patient_id": "patient-123",
            "title": "Diagram 1",
            "category": "clinical-diagram",
        },
    )
    
    client.post(
        "/api/v1/excalidraw/diagrams",
        json={
            "diagram_data": diagram_data,
            "patient_id": "patient-123",
            "title": "Diagram 2",
            "category": "education",
        },
    )
    
    # List all diagrams
    response = client.get("/api/v1/excalidraw/patients/patient-123/diagrams")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    
    # List filtered by category
    response = client.get(
        "/api/v1/excalidraw/patients/patient-123/diagrams?category=clinical-diagram"
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Diagram 1"


def test_update_diagram(client: TestClient, diagram_data):
    """Test updating a diagram via API."""
    # Create diagram
    create_response = client.post(
        "/api/v1/excalidraw/diagrams",
        json={
            "diagram_data": diagram_data,
            "patient_id": "patient-123",
            "title": "Original Title",
        },
    )
    
    media_id = create_response.json()["media_id"]
    
    # Update diagram
    updated_data = diagram_data.copy()
    updated_data["elements"].append({
        "id": "element2",
        "type": "ellipse",
        "x": 300,
        "y": 200,
        "width": 100,
        "height": 100,
    })
    
    response = client.put(
        f"/api/v1/excalidraw/diagrams/{media_id}",
        json={
            "diagram_data": updated_data,
            "title": "Updated Title",
        },
    )
    
    assert response.status_code == 200
    
    # Verify update
    get_response = client.get(f"/api/v1/excalidraw/diagrams/{media_id}")
    data = get_response.json()
    assert data["title"] == "Updated Title"
    assert len(data["data"]["elements"]) == 2


def test_delete_diagram(client: TestClient, diagram_data):
    """Test deleting a diagram via API."""
    # Create diagram
    create_response = client.post(
        "/api/v1/excalidraw/diagrams",
        json={
            "diagram_data": diagram_data,
            "patient_id": "patient-123",
            "title": "To Delete",
        },
    )
    
    media_id = create_response.json()["media_id"]
    
    # Delete diagram
    response = client.delete(f"/api/v1/excalidraw/diagrams/{media_id}")
    
    assert response.status_code == 204
    
    # Verify deletion
    get_response = client.get(f"/api/v1/excalidraw/diagrams/{media_id}")
    assert get_response.status_code == 404

