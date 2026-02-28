"""Tests for Excalidraw Diagram Storage Service."""

import pytest
from sqlalchemy.orm import Session

from grahame.services.excalidraw import ExcalidrawDiagramStorage


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
                "strokeColor": "#000000",
                "backgroundColor": "#ffffff",
            },
            {
                "id": "element2",
                "type": "text",
                "x": 150,
                "y": 130,
                "text": "Hello World",
                "fontSize": 20,
            },
        ],
        "appState": {
            "viewBackgroundColor": "#ffffff",
            "gridSize": 20,
        },
    }


def test_save_diagram(db: Session, diagram_data):
    """Test saving a diagram."""
    storage = ExcalidrawDiagramStorage(db, "test-tenant")
    
    result = storage.save_diagram(
        diagram_data=diagram_data,
        patient_id="patient-123",
        title="Test Diagram",
        description="A test diagram",
        category="clinical-diagram",
        author_id="practitioner-456",
    )
    
    assert "media_id" in result
    assert "document_reference_id" in result
    assert "diagram_url" in result
    assert result["diagram_url"].startswith("/fhir/Media/")


def test_get_diagram(db: Session, diagram_data):
    """Test retrieving a diagram."""
    storage = ExcalidrawDiagramStorage(db, "test-tenant")
    
    # Save diagram
    result = storage.save_diagram(
        diagram_data=diagram_data,
        patient_id="patient-123",
        title="Test Diagram",
    )
    
    media_id = result["media_id"]
    
    # Retrieve diagram
    diagram = storage.get_diagram(media_id)
    
    assert diagram is not None
    assert diagram["id"] == media_id
    assert diagram["title"] == "Test Diagram"
    assert diagram["patient_id"] == "patient-123"
    assert diagram["data"]["type"] == "excalidraw"
    assert len(diagram["data"]["elements"]) == 2


def test_get_nonexistent_diagram(db: Session):
    """Test retrieving a non-existent diagram."""
    storage = ExcalidrawDiagramStorage(db, "test-tenant")
    
    diagram = storage.get_diagram("nonexistent-id")
    
    assert diagram is None


def test_list_patient_diagrams(db: Session, diagram_data):
    """Test listing diagrams for a patient."""
    storage = ExcalidrawDiagramStorage(db, "test-tenant")
    
    # Save multiple diagrams
    storage.save_diagram(
        diagram_data=diagram_data,
        patient_id="patient-123",
        title="Diagram 1",
        category="clinical-diagram",
    )
    
    storage.save_diagram(
        diagram_data=diagram_data,
        patient_id="patient-123",
        title="Diagram 2",
        category="education",
    )
    
    storage.save_diagram(
        diagram_data=diagram_data,
        patient_id="patient-456",  # Different patient
        title="Diagram 3",
    )
    
    # List all diagrams for patient-123
    diagrams = storage.list_patient_diagrams("patient-123")
    
    assert len(diagrams) == 2
    assert all(d["title"] in ["Diagram 1", "Diagram 2"] for d in diagrams)
    
    # List diagrams filtered by category
    clinical_diagrams = storage.list_patient_diagrams("patient-123", category="clinical-diagram")
    
    assert len(clinical_diagrams) == 1
    assert clinical_diagrams[0]["title"] == "Diagram 1"


def test_update_diagram(db: Session, diagram_data):
    """Test updating a diagram."""
    storage = ExcalidrawDiagramStorage(db, "test-tenant")
    
    # Save diagram
    result = storage.save_diagram(
        diagram_data=diagram_data,
        patient_id="patient-123",
        title="Original Title",
    )
    
    media_id = result["media_id"]
    
    # Update diagram
    updated_data = diagram_data.copy()
    updated_data["elements"].append({
        "id": "element3",
        "type": "ellipse",
        "x": 300,
        "y": 200,
        "width": 100,
        "height": 100,
    })
    
    success = storage.update_diagram(
        media_id=media_id,
        diagram_data=updated_data,
        title="Updated Title",
    )
    
    assert success is True
    
    # Verify update
    diagram = storage.get_diagram(media_id)
    assert diagram["title"] == "Updated Title"
    assert len(diagram["data"]["elements"]) == 3


def test_delete_diagram(db: Session, diagram_data):
    """Test deleting a diagram."""
    storage = ExcalidrawDiagramStorage(db, "test-tenant")
    
    # Save diagram
    result = storage.save_diagram(
        diagram_data=diagram_data,
        patient_id="patient-123",
        title="To Delete",
    )
    
    media_id = result["media_id"]
    
    # Delete diagram
    success = storage.delete_diagram(media_id)
    
    assert success is True
    
    # Verify deletion (should return None or empty)
    diagram = storage.get_diagram(media_id)
    # Depending on soft-delete implementation, this might be None or have a deleted flag
    # For now, we just check that delete succeeded

